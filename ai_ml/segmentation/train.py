import os
import sys
import csv
import time
import random
import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

# Ensure D:/slideland is in search path
sys.path.append("D:/slideland")

from ai_ml.segmentation.dataset import LandslideDataset
from ai_ml.segmentation.model import UNet
from ai_ml.segmentation.losses import CombinedLoss
from ai_ml.segmentation.evaluate import compute_metrics
from ai_ml.segmentation.predict import predict_single_image

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0
    for images, masks, _ in dataloader:
        images = images.to(device)
        masks = masks.to(device).unsqueeze(1) # shape (B, 1, H, W)
        
        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, masks)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
    return running_loss / len(dataloader.dataset)

def evaluate_validation(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_probs = []
    all_targets = []
    
    with torch.no_grad():
        for images, masks, _ in dataloader:
            images = images.to(device)
            masks_expanded = masks.to(device).unsqueeze(1)
            
            logits = model(images)
            loss = criterion(logits, masks_expanded)
            running_loss += loss.item() * images.size(0)
            
            probs = torch.sigmoid(logits).squeeze(1) # shape (B, H, W)
            all_probs.append(probs.cpu().numpy())
            all_targets.append(masks.numpy())
            
    val_loss = running_loss / len(dataloader.dataset)
    all_probs = np.concatenate(all_probs, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)
    
    metrics = compute_metrics(all_probs, all_targets)
    metrics["loss"] = val_loss
    return metrics, all_probs, all_targets

def save_qualitative_predictions(model, dataset, val_files, device, num_samples=5):
    """
    Saves visual predictions of 5 validation files to D:/slideland/ai_ml/models/baseline_predictions/
    """
    output_dir = "D:/slideland/ai_ml/models/baseline_predictions"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save predictions for first few files
    for i in range(min(num_samples, len(val_files))):
        img_name = val_files[i]
        
        # Find item index in dataset
        idx = dataset.filenames.index(img_name)
        img_tensor, mask_tensor, _ = dataset[idx]
        
        # Prepare for prediction
        model.eval()
        img_numpy = img_tensor.numpy()
        
        # Run predictor
        pred_res = predict_single_image(model, img_numpy, device=device)
        prob_map = pred_res["probability_map"]
        bin_mask = pred_res["binary_mask"]
        
        # Plotting
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        
        # 1. Input visualization: DEM channel (Index 13)
        # Un-normalize DEM band for visual clarity
        dem_channel = img_numpy[13]
        dem_mean = -0.4914  # approximation or direct band extraction
        # Just use direct raw values scaled to [0, 1] for visualization
        dem_min, dem_max = dem_channel.min(), dem_channel.max()
        if dem_max > dem_min:
            dem_vis = (dem_channel - dem_min) / (dem_max - dem_min)
        else:
            dem_vis = dem_channel
            
        axes[0].imshow(dem_vis, cmap="terrain")
        axes[0].set_title("DEM (Topography)")
        axes[0].axis("off")
        
        # 2. Ground Truth Mask
        axes[1].imshow(mask_tensor.numpy(), cmap="gray", vmin=0, vmax=1)
        axes[1].set_title("Ground Truth Mask")
        axes[1].axis("off")
        
        # 3. Probability Map
        im = axes[2].imshow(prob_map, cmap="jet", vmin=0, vmax=1)
        axes[2].set_title("Predicted Prob Map")
        axes[2].axis("off")
        
        # 4. Binary Mask
        axes[3].imshow(bin_mask, cmap="gray", vmin=0, vmax=1)
        axes[3].set_title(f"Binary Mask ({pred_res['landslide_area_percent']:.1f}%)")
        axes[3].axis("off")
        
        fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04)
        plt.tight_layout()
        
        save_path = os.path.join(output_dir, f"prediction_{img_name.replace('.h5', '.png')}")
        plt.savefig(save_path, dpi=150)
        plt.close()
    print(f"Visualized {num_samples} holdout predictions in: {output_dir}")

def run_training(epochs=20, batch_size=16, patience=5):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Starting training pipeline on device: {device}")
    
    # 1. Load filenames and split
    # Since dataset_dir is configurable, we get it from standard defaults
    dataset_temp = LandslideDataset(split="train")
    all_files = dataset_temp.filenames
    
    # Deterministic Shuffle
    random.shuffle(all_files)
    
    # 80/20 train/holdout split
    split_idx = int(0.8 * len(all_files))
    train_files = all_files[:split_idx]
    val_files = all_files[split_idx:]
    
    print(f"Dataset split completed:")
    print(f"  Total samples: {len(all_files)}")
    print(f"  Training samples: {len(train_files)}")
    print(f"  Validation samples: {len(val_files)}")
    
    # Save split log lists
    os.makedirs("D:/slideland/ai_ml/models", exist_ok=True)
    with open("D:/slideland/ai_ml/models/train_split.txt", "w") as f:
        f.write("\n".join(train_files))
    with open("D:/slideland/ai_ml/models/val_split.txt", "w") as f:
        f.write("\n".join(val_files))
        
    # 2. Build Datasets
    train_dataset = LandslideDataset(split="train", filenames=train_files, augment=True)
    val_dataset = LandslideDataset(split="train", filenames=val_files, augment=False)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # 3. Model, Criterion, Optimizer
    model = UNet(n_channels=14, n_classes=1).to(device)
    criterion = CombinedLoss(bce_weight=0.5, dice_weight=0.5)
    # Adam parameters from Landslide4Sense baseline
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=5e-4)
    
    # 4. Training Loop setup
    best_f1 = -1.0
    best_epoch = -1
    epochs_no_improve = 0
    history = []
    
    print(f"Training for up to {epochs} epochs...")
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Train one epoch
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
        
        # Evaluate validation
        val_metrics, _, _ = evaluate_validation(model, val_loader, criterion, device)
        
        epoch_elapsed = time.time() - epoch_start
        val_f1 = val_metrics["f1_score"]
        
        epoch_record = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_metrics["loss"],
            "overall_accuracy": val_metrics["overall_accuracy"],
            "precision": val_metrics["precision"],
            "recall": val_metrics["recall"],
            "f1_score": val_f1,
            "iou": val_metrics["iou"],
            "time_seconds": epoch_elapsed
        }
        history.append(epoch_record)
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_metrics['loss']:.4f} | "
              f"Val F1: {val_f1:.4f} | Val IoU: {val_metrics['iou']:.4f} | Accuracy: {val_metrics['overall_accuracy']:.4f} | "
              f"Time: {epoch_elapsed:.1f}s")
              
        # Checkpoint based on F1 score
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_epoch = epoch + 1
            epochs_no_improve = 0
            torch.save(model.state_dict(), "D:/slideland/ai_ml/models/baseline_unet_best.pth")
            print(f"  *** Best model updated (Validation F1 = {best_f1:.4f})")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"  Early stopping triggered! No validation F1 improvement for {patience} epochs.")
                break
                
    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time:.1f} seconds. Best Epoch: {best_epoch} with Validation F1: {best_f1:.4f}")
    
    # 5. Save history to CSV
    csv_path = "D:/slideland/ai_ml/models/baseline_training_history.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
    print(f"Training history saved to: {csv_path}")
    
    # 6. Load Best Checkpoint and Run Holdout Evaluation
    print("\nRunning final Holdout Evaluation using the best checkpoint...")
    best_model = UNet(n_channels=14, n_classes=1).to(device)
    best_model.load_state_dict(torch.load("D:/slideland/ai_ml/models/baseline_unet_best.pth"))
    
    final_metrics, probs, targets = evaluate_validation(best_model, val_loader, criterion, device)
    
    # Pixel stats
    total_pixels = int(targets.size)
    landslide_pixels = int(np.sum(targets == 1))
    non_landslide_pixels = int(np.sum(targets == 0))
    
    binary_preds = (probs >= 0.5).astype(np.uint8)
    predicted_landslide_pixels = int(np.sum(binary_preds == 1))
    
    print("\n=== FINAL HOLDOUT METRICS (LANDSLIDE CLASS) ===")
    print(f"  Loss: {final_metrics['loss']:.4f}")
    print(f"  Overall Accuracy: {final_metrics['overall_accuracy']:.4f}")
    print(f"  Precision: {final_metrics['precision']:.4f}")
    print(f"  Recall: {final_metrics['recall']:.4f}")
    print(f"  F1 Score: {final_metrics['f1_score']:.4f}")
    print(f"  Intersection over Union (IoU): {final_metrics['iou']:.4f}")
    print(f"\n=== PIXEL STATISTICS ===")
    print(f"  Total Validation Pixels: {total_pixels}")
    print(f"  True Landslide Pixels: {landslide_pixels} ({landslide_pixels/total_pixels*100:.2f}%)")
    print(f"  True Non-Landslide Pixels: {non_landslide_pixels} ({non_landslide_pixels/total_pixels*100:.2f}%)")
    print(f"  Predicted Landslide Pixels: {predicted_landslide_pixels} ({predicted_landslide_pixels/total_pixels*100:.2f}%)")
    
    # Save qualitative visual predictions
    # We pass val_dataset (augment=False) to visualize static validation samples
    save_qualitative_predictions(best_model, val_dataset, val_files, device, num_samples=5)
    
    return {
        "device": str(device),
        "total_time": total_time,
        "best_epoch": best_epoch,
        "train_samples": len(train_files),
        "holdout_samples": len(val_files),
        "metrics": final_metrics,
        "pixel_stats": {
            "total": total_pixels,
            "true_landslide": landslide_pixels,
            "true_non_landslide": non_landslide_pixels,
            "predicted_landslide": predicted_landslide_pixels
        }
    }

if __name__ == "__main__":
    # Allows running directly via shell command
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--patience", type=int, default=5)
    args = parser.parse_args()
    
    run_training(epochs=args.epochs, batch_size=args.batch_size, patience=args.patience)
