import numpy as np
import torch

def compute_metrics(preds, targets, threshold=0.5, epsilon=1e-7):
    """
    Computes semantic segmentation metrics.
    preds: (N, H, W) sigmoid probabilities or logits
    targets: (N, H, W) binary labels (0 or 1)
    """
    if isinstance(preds, torch.Tensor):
        preds = preds.detach().cpu().numpy()
    if isinstance(targets, torch.Tensor):
        targets = targets.detach().cpu().numpy()

    # Apply threshold to get binary predictions
    binary_preds = (preds >= threshold).astype(np.uint8)
    binary_targets = (targets >= threshold).astype(np.uint8)

    # Flatten arrays for confusion matrix
    y_pred = binary_preds.ravel()
    y_true = binary_targets.ravel()

    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))

    # Overall Accuracy
    accuracy = (tp + tn) / (tp + tn + fp + fn + epsilon)

    # Precision (Landslide Class)
    precision = tp / (tp + fp + epsilon)

    # Recall (Landslide Class)
    recall = tp / (tp + fn + epsilon)

    # F1 Score (Landslide Class)
    f1_score = 2.0 * precision * recall / (precision + recall + epsilon)

    # Intersection over Union (IoU / Jaccard Index)
    iou = tp / (tp + fp + fn + epsilon)

    return {
        "overall_accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score),
        "iou": float(iou)
    }
