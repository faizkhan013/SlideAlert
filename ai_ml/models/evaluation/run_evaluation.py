import os
import sys
import csv
import time
import numpy as np
import torch
import matplotlib.pyplot as plt

# Ensure D:/slideland is in search path
sys.path.append("D:/slideland")

from ai_ml.segmentation.dataset import LandslideDataset
from ai_ml.segmentation.model import UNet
from ai_ml.segmentation.losses import CombinedLoss

def calculate_metrics_for_threshold(all_probs, all_targets, threshold=0.5, epsilon=1e-7):
    """
    Computes metrics at a given threshold, handling edge cases where actual/predicted
    positives are zero to prevent division-by-zero or NaN issues.
    """
    binary_preds = (all_probs >= threshold).astype(np.uint8)
    binary_targets = (all_targets >= threshold).astype(np.uint8)
    
    y_pred = binary_preds.ravel()
    y_true = binary_targets.ravel()
    
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    
    # Overall Accuracy: (TP + TN) / Total
    accuracy = (tp + tn) / (tp + tn + fp + fn + epsilon)
    
    # Precision: TP / (TP + FP)
    # If there are no positive predictions, check if actual positive is also zero
    if tp + fp == 0:
        precision = 1.0 if (tp + fn == 0) else 0.0
    else:
        precision = tp / (tp + fp)
        
    # Recall: TP / (TP + FN)
    # If there are no positive actuals, check if prediction is also empty
    if tp + fn == 0:
        recall = 1.0 if (tp + fp == 0) else 0.0
    else:
        recall = tp / (tp + fn)
        
    # F1 / Dice: 2 * P * R / (P + R)
    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2.0 * precision * recall / (precision + recall)
        
    # IoU: TP / (TP + FP + FN)
    if tp + fp + fn == 0:
        iou = 1.0
    else:
        iou = tp / (tp + fp + fn)
        
    dice = f1_score # Mathematically identical for binary segmentation
    
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score),
        "iou": float(iou),
        "dice": float(dice),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn
    }

def main():
    checkpoint_path = "D:/slideland/ai_ml/models/baseline_unet_best.pth"
    val_split_path = "D:/slideland/ai_ml/models/val_split.txt"
    eval_dir = "D:/slideland/ai_ml/models/evaluation"
    examples_dir = os.path.join(eval_dir, "examples")
    
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(examples_dir, exist_ok=True)
    
    if not os.path.exists(checkpoint_path):
        print(f"Error: checkpoint not found at {checkpoint_path}")
        sys.exit(1)
        
    checkpoint_size = os.path.getsize(checkpoint_path)
    
    if not os.path.exists(val_split_path):
        print(f"Error: validation split file not found at {val_split_path}")
        sys.exit(1)
        
    with open(val_split_path, "r") as f:
        val_files = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(val_files)} validation files.")
    
    # Initialize dataset and model
    dataset = LandslideDataset(split="train", filenames=val_files, augment=False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = UNet(n_channels=14, n_classes=1)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.to(device)
    model.eval()
    
    criterion = CombinedLoss(bce_weight=0.5, dice_weight=0.5)
    
    all_probs = []
    all_targets = []
    
    start_time = time.time()
    inference_times = []
    total_loss = 0.0
    
    print("Running inference across validation set...")
    with torch.no_grad():
        for i in range(len(dataset)):
            img_tensor, mask_tensor, _ = dataset[i]
            
            t0 = time.time()
            img_batch = img_tensor.unsqueeze(0).to(device) # Shape (1, 14, 128, 128)
            logits = model(img_batch)
            probs = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy() # Shape (128, 128)
            inference_times.append(time.time() - t0)
            
            # Compute loss
            mask_batch = mask_tensor.unsqueeze(0).unsqueeze(0).to(device) # Shape (1, 1, 128, 128)
            loss_val = criterion(logits, mask_batch).item()
            total_loss += loss_val * img_batch.size(0)
            
            all_probs.append(probs)
            all_targets.append(mask_tensor.numpy())
            
    eval_elapsed = time.time() - start_time
    avg_inf_time = np.mean(inference_times)
    mean_val_loss = total_loss / len(dataset)
    
    all_probs = np.stack(all_probs, axis=0) # (N, 128, 128)
    all_targets = np.stack(all_targets, axis=0) # (N, 128, 128)
    
    # Pixel counts and distribution
    total_pixels = all_targets.size
    landslide_pixels = int(np.sum(all_targets == 1))
    non_landslide_pixels = int(np.sum(all_targets == 0))
    pct_landslide = (landslide_pixels / total_pixels) * 100
    
    print("\n--- Pixel Distribution Analysis ---")
    print(f"Total Pixels: {total_pixels}")
    print(f"Landslide (Positive): {landslide_pixels} ({pct_landslide:.2f}%)")
    print(f"Non-Landslide (Negative): {non_landslide_pixels} ({100-pct_landslide:.2f}%)")
    print(f"Average Validation Loss (BCE + Dice): {mean_val_loss:.4f}")
    
    # Evaluate over thresholds [0.30, 0.40, 0.50, 0.60, 0.70]
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    threshold_results = []
    
    print("\nEvaluating different thresholds...")
    for t in thresholds:
        metrics = calculate_metrics_for_threshold(all_probs, all_targets, threshold=t)
        threshold_results.append((t, metrics))
        print(f"Threshold {t:.2f}: Accuracy={metrics['accuracy']:.4f}, Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, F1={metrics['f1_score']:.4f}, IoU={metrics['iou']:.4f}")
        
    # Write threshold comparison to CSV
    threshold_csv_path = os.path.join(eval_dir, "threshold_comparison.csv")
    with open(threshold_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["threshold", "accuracy", "precision", "recall", "f1_score", "iou", "dice", "tp", "fp", "fn", "tn"])
        for t, m in threshold_results:
            writer.writerow([f"{t:.2f}", m["accuracy"], m["precision"], m["recall"], m["f1_score"], m["iou"], m["dice"], m["tp"], m["fp"], m["fn"], m["tn"]])
    print(f"Saved threshold comparison to {threshold_csv_path}")
    
    # Baseline threshold metrics
    baseline_t = 0.50
    baseline_metrics = next(m for t, m in threshold_results if abs(t - baseline_t) < 1e-4)
    
    # Save final baseline metrics to CSV
    metrics_path = os.path.join(eval_dir, "final_metrics.csv")
    with open(metrics_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["loss", mean_val_loss])
        writer.writerow(["accuracy", baseline_metrics["accuracy"]])
        writer.writerow(["precision", baseline_metrics["precision"]])
        writer.writerow(["recall", baseline_metrics["recall"]])
        writer.writerow(["f1_score", baseline_metrics["f1_score"]])
        writer.writerow(["iou", baseline_metrics["iou"]])
        writer.writerow(["dice", baseline_metrics["dice"]])
        writer.writerow(["threshold", baseline_t])
        writer.writerow(["num_samples", len(val_files)])
        writer.writerow(["total_pixels", total_pixels])
        writer.writerow(["landslide_pixels", landslide_pixels])
        writer.writerow(["non_landslide_pixels", non_landslide_pixels])
        writer.writerow(["percentage_landslide_pixels", pct_landslide])
        writer.writerow(["tp", baseline_metrics["tp"]])
        writer.writerow(["fp", baseline_metrics["fp"]])
        writer.writerow(["fn", baseline_metrics["fn"]])
        writer.writerow(["tn", baseline_metrics["tn"]])
        writer.writerow(["checkpoint_size_bytes", checkpoint_size])
        writer.writerow(["device", str(device)])
        writer.writerow(["evaluation_time_seconds", eval_elapsed])
        writer.writerow(["average_inference_time_seconds", avg_inf_time])
    print(f"Saved baseline metrics to {metrics_path}")
    
    # Save confusion matrix at 0.50
    cm_path = os.path.join(eval_dir, "confusion_matrix.csv")
    with open(cm_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["actual_class", "predicted_non_landslide", "predicted_landslide"])
        writer.writerow(["actual_non_landslide", baseline_metrics["tn"], baseline_metrics["fp"]])
        writer.writerow(["actual_landslide", baseline_metrics["fn"], baseline_metrics["tp"]])
    print(f"Saved confusion matrix to {cm_path}")
    
    # Qualitative predictions (10 examples)
    # Deterministically select first 10 validation files
    sample_files = val_files[:10]
    print(f"\nGenerating visual overlays for first 10 validation files...")
    for idx, fname in enumerate(sample_files):
        # Retrieve index in dataset
        ds_idx = dataset.filenames.index(fname)
        img_tensor, mask_tensor, _ = dataset[ds_idx]
        
        # Inference
        img_batch = img_tensor.unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(img_batch)
            prob_map = torch.sigmoid(logits).squeeze(0).squeeze(0).cpu().numpy()
            
        bin_mask = (prob_map >= baseline_t).astype(np.uint8)
        gt_mask = mask_tensor.numpy().astype(np.uint8)
        
        # Extract DEM (index 13) for terrain representation
        img_numpy = img_tensor.numpy()
        dem_channel = img_numpy[13]
        dem_min, dem_max = dem_channel.min(), dem_channel.max()
        if dem_max > dem_min:
            dem_vis = (dem_channel - dem_min) / (dem_max - dem_min)
        else:
            dem_vis = dem_channel
            
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        
        # 1. Input Terrain (DEM)
        axes[0].imshow(dem_vis, cmap="terrain")
        axes[0].set_title(f"DEM Input ({fname})")
        axes[0].axis("off")
        
        # 2. Ground Truth Mask
        axes[1].imshow(gt_mask, cmap="gray", vmin=0, vmax=1)
        axes[1].set_title(f"Ground Truth ({np.sum(gt_mask==1)} px)")
        axes[1].axis("off")
        
        # 3. Probability Map
        im = axes[2].imshow(prob_map, cmap="jet", vmin=0, vmax=1)
        axes[2].set_title("Probability Map")
        axes[2].axis("off")
        
        # 4. Predicted Mask & Overlay
        # Display overlay of predicted mask over DEM
        overlay = np.zeros((*bin_mask.shape, 3))
        overlay[..., 0] = bin_mask * 1.0 # Red channel for predictions
        overlay[..., 1] = gt_mask * 1.0  # Green channel for targets
        # Overlay colors:
        # Red (predicted but not ground truth) = False Positive
        # Green (ground truth but not predicted) = False Negative
        # Yellow (both predicted and ground truth) = True Positive
        axes[3].imshow(overlay)
        axes[3].set_title("Overlay (R=FP, G=FN, Y=TP)")
        axes[3].axis("off")
        
        fig.colorbar(im, ax=axes[2], fraction=0.046, pad=0.04)
        plt.tight_layout()
        
        save_path = os.path.join(examples_dir, f"example_{fname.replace('.h5', '.png')}")
        plt.savefig(save_path, dpi=150)
        plt.close()
        print(f"Saved qualitative prediction visual {idx+1}/10 to {save_path}")
        
    print("\nModel evaluation completed successfully!")

if __name__ == "__main__":
    main()
