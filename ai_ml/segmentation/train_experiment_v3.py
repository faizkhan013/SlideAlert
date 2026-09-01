import os
import sys
import csv
import time
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

# Ensure search path is root
sys.path.append("D:/slideland")

from ai_ml.segmentation.dataset import LandslideDataset
from ai_ml.segmentation.model import UNet
from ai_ml.segmentation.losses import DiceLoss
from ai_ml.segmentation.evaluate import compute_metrics

# Loss Functions
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits, targets):
        bce_loss = F.binary_cross_entropy_with_logits(logits, targets, reduction='none')
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1 - probs) * (1 - targets)
        loss = bce_loss * ((1 - p_t) ** self.gamma)
        
        if self.alpha >= 0:
            alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
            loss = alpha_t * loss
            
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

class FocalDiceLoss(nn.Module):
    def __init__(self, focal_weight=0.5, dice_weight=0.5, alpha=0.25, gamma=2.0):
        super().__init__()
        self.focal_weight = focal_weight
        self.dice_weight = dice_weight
        self.focal = FocalLoss(alpha=alpha, gamma=gamma)
        self.dice = DiceLoss()

    def forward(self, logits, targets):
        return self.focal_weight * self.focal(logits, targets) + self.dice_weight * self.dice(logits, targets)

# Seed Setup
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

def run_experiment_v3(epochs=10, batch_size=16, patience=3):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Starting Experiment 3 training on device: {device}")
    
    train_split_path = "D:/slideland/ai_ml/models/train_split.txt"
    val_split_path = "D:/slideland/ai_ml/models/val_split.txt"
    
    with open(train_split_path, "r") as f:
        train_files = [line.strip() for line in f if line.strip()]
    with open(val_split_path, "r") as f:
        val_files = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded splits:")
    print(f"  Training samples: {len(train_files)}")
    print(f"  Validation samples: {len(val_files)}")
    
    train_dataset = LandslideDataset(split="train", filenames=train_files, augment=True)
    val_dataset = LandslideDataset(split="train", filenames=val_files, augment=False)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    model = UNet(n_channels=14, n_classes=1).to(device)
    criterion = FocalDiceLoss(focal_weight=0.5, dice_weight=0.5, alpha=0.25, gamma=2.0)
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=5e-4)
    
    best_val_loss = float("inf")
    best_epoch = -1
    epochs_no_improve = 0
    history = []
    
    exp_model_dir = "D:/slideland/ai_ml/models/experiments/improved_unet"
    exp_csv_dir = "D:/slideland/ai_ml/models/evaluation/experiments/improved_unet"
    os.makedirs(exp_model_dir, exist_ok=True)
    os.makedirs(exp_csv_dir, exist_ok=True)
    
    checkpoint_save_path = os.path.join(exp_model_dir, "improved_unet_v3_best.pth")
    print(f"Experimental Checkpoint path: {checkpoint_save_path}")
    
    if checkpoint_save_path == "D:/slideland/ai_ml/models/baseline_unet_best.pth":
        raise ValueError("CRITICAL ERROR: Save path matches baseline path!")
        
    print(f"Training for up to {epochs} epochs with patience {patience} based on Validation Loss...")
    start_time = time.time()
    
    for epoch in range(epochs):
        epoch_start = time.time()
        
        train_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_metrics, _, _ = evaluate_validation(model, val_loader, criterion, device)
        
        epoch_elapsed = time.time() - epoch_start
        val_loss = val_metrics["loss"]
        val_f1 = val_metrics["f1_score"]
        val_iou = val_metrics["iou"]
        
        epoch_record = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "f1_score": val_f1,
            "iou": val_iou
        }
        history.append(epoch_record)
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
              f"Val F1: {val_f1:.4f} | Val IoU: {val_iou:.4f} | Accuracy: {val_metrics['overall_accuracy']:.4f} | "
              f"Time: {epoch_elapsed:.1f}s")
              
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch + 1
            epochs_no_improve = 0
            torch.save(model.state_dict(), checkpoint_save_path)
            print(f"  *** Best experimental model updated (Validation Loss = {best_val_loss:.4f})")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"  Early stopping triggered after {epoch+1} epochs.")
                break
                
    total_time = time.time() - start_time
    print(f"\nTraining completed in {total_time:.1f} seconds. Best Epoch: {best_epoch} with Val Loss: {best_val_loss:.4f}")
    
    # Save training log
    csv_path = os.path.join(exp_csv_dir, "v3_training_history.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
        
    # 5. Load best experimental v3 model and run holdout evaluation
    print("\nRunning final Holdout Evaluation using the best Experiment 3 checkpoint...")
    best_model = UNet(n_channels=14, n_classes=1).to(device)
    best_model.load_state_dict(torch.load(checkpoint_save_path))
    best_model.eval()
    
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    comparison_records = []
    
    _, probs, targets = evaluate_validation(best_model, val_loader, criterion, device)
    total_pixels = int(targets.size)
    
    for t in thresholds:
        preds = (probs >= t).astype(np.uint8)
        
        tp = int(np.sum((preds == 1) & (targets == 1)))
        fp = int(np.sum((preds == 1) & (targets == 0)))
        fn = int(np.sum((preds == 0) & (targets == 1)))
        tn = int(np.sum((preds == 0) & (targets == 0)))
        
        accuracy = (tp + tn) / total_pixels
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
        
        comparison_records.append({
            "threshold": f"{t:.2f}",
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "iou": iou,
            "dice": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn
        })
        
        if abs(t - 0.5) < 0.01:
            final_metrics_path = os.path.join(exp_csv_dir, "v3_metrics.csv")
            with open(final_metrics_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "value"])
                writer.writerow(["loss", best_val_loss])
                writer.writerow(["accuracy", accuracy])
                writer.writerow(["precision", precision])
                writer.writerow(["recall", recall])
                writer.writerow(["f1_score", f1])
                writer.writerow(["iou", iou])
                writer.writerow(["dice", f1])
                writer.writerow(["threshold", t])
                writer.writerow(["tp", tp])
                writer.writerow(["fp", fp])
                writer.writerow(["fn", fn])
                writer.writerow(["tn", tn])
                writer.writerow(["best_epoch", best_epoch])
                
            confusion_matrix_path = os.path.join(exp_csv_dir, "v3_confusion_matrix.csv")
            with open(confusion_matrix_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["actual_class", "predicted_non_landslide", "predicted_landslide"])
                writer.writerow(["actual_non_landslide", tn, fp])
                writer.writerow(["actual_landslide", fn, tp])
                
    # Save threshold comparison
    threshold_comparison_path = os.path.join(exp_csv_dir, "v3_threshold_comparison.csv")
    with open(threshold_comparison_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=comparison_records[0].keys())
        writer.writeheader()
        writer.writerows(comparison_records)
        
    print(f"Experiment 3 evaluation outputs successfully written to: {exp_csv_dir}")

if __name__ == "__main__":
    run_experiment_v3(epochs=10, batch_size=16, patience=3)
