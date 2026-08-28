import os
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset
from ..preprocessing.normalization import BandNormalizer

# Path configuration based on workspace structures and environment variables
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATASET_ROOT = os.path.join(PROJECT_ROOT, "dataset", "Landslide4Sense")
DATASET_ROOT = os.getenv("LANDSLIDE4SENSE_DATA_DIR", DEFAULT_DATASET_ROOT)

class LandslideDataset(Dataset):
    """
    PyTorch dataset for reading Landslide4Sense HDF5 image and mask files.
    """
    def __init__(self, dataset_dir=None, split="train", filenames=None, augment=False):
        """
        split: 'train' or 'valid'
        filenames: optional list of h5 files to use
        augment: whether to apply random spatial augmentations
        """
        self.dataset_dir = dataset_dir if dataset_dir else DATASET_ROOT
        self.split = split
        self.augment = augment
        self.normalizer = BandNormalizer()
        
        if split == "train":
            self.data_dir = os.path.join(self.dataset_dir, "TrainData")
        elif split == "valid":
            self.data_dir = os.path.join(self.dataset_dir, "ValidData")
        else:
            raise ValueError(f"Unknown split: {split}")
            
        self.img_dir = os.path.join(self.data_dir, "img")
        self.mask_dir = os.path.join(self.data_dir, "mask")
        
        if not os.path.exists(self.img_dir):
            raise FileNotFoundError(f"Image directory not found: {self.img_dir}")
            
        # Get sorted list of files or use custom filenames list
        if filenames is not None:
            self.filenames = filenames
        else:
            self.filenames = sorted([f for f in os.listdir(self.img_dir) if f.endswith(".h5")])

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):
        img_name = self.filenames[idx]
        img_path = os.path.join(self.img_dir, img_name)
        
        # Load image
        with h5py.File(img_path, "r") as hf:
            image = hf["img"][:]  # Shape (128, 128, 14), float64
            
        # Convert to float32 and shape (14, 128, 128)
        image = np.asarray(image, np.float32)
        image = image.transpose((-1, 0, 1))
        
        # Load mask if it exists
        mask_name = img_name.replace("image_", "mask_")
        mask_path = os.path.join(self.mask_dir, mask_name)
        
        has_mask = os.path.exists(mask_path)
        if has_mask:
            with h5py.File(mask_path, "r") as hf:
                mask = hf["mask"][:]  # Shape (128, 128), uint8
            mask = np.asarray(mask, np.float32)
        else:
            mask = None
            
        # Apply spatial augmentations (only if augment is enabled and mask exists)
        if self.augment and mask is not None:
            # 1. Random Horizontal Flip (p=0.5)
            if np.random.rand() > 0.5:
                image = np.flip(image, axis=2)
                mask = np.flip(mask, axis=1)
                
            # 2. Random Vertical Flip (p=0.5)
            if np.random.rand() > 0.5:
                image = np.flip(image, axis=1)
                mask = np.flip(mask, axis=0)
                
            # 3. Random 90-degree rotations (k = 0, 90, 180, 270)
            k = np.random.randint(0, 4)
            if k > 0:
                image = np.rot90(image, k, axes=(1, 2))
                mask = np.rot90(mask, k, axes=(0, 1))

        # Normalize image
        image = self.normalizer.normalize_numpy(image)
        
        # Convert to tensors (using copy to prevent negative strides errors in PyTorch)
        image_tensor = torch.from_numpy(image.copy())
        if mask is not None:
            mask_tensor = torch.from_numpy(mask.copy())
        else:
            mask_tensor = torch.empty(0)
            
        return image_tensor, mask_tensor, img_name
