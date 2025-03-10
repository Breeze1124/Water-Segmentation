import os
import torch
import numpy as np
from PIL import Image
import random

class WaterBodiesDataset(torch.utils.data.Dataset):
    def __init__(self, root, mode="train", transform=None):

        assert mode in {"train", "val", "test", "all"}

        self.root = root
        self.mode = mode
        self.transform = transform

        mode_dir = "trainset"
        self.images_directory = os.path.join(self.root, f"{mode_dir}/images")
        self.masks_directory = os.path.join(self.root, f"{mode_dir}/masks")

        self.filenames = self._read_split()  # read train/valid/test splits

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):
        
        filename = self.filenames[idx]
        image_path = os.path.join(self.images_directory, filename + ".png")
        mask_path = os.path.join(self.masks_directory, filename + ".png")

        image = np.array(Image.open(image_path).convert("RGB"))

        trimap = np.array(Image.open(mask_path))
        mask = self._preprocess_mask(trimap)

        sample = dict(image=image, mask=mask)

        return sample

    @staticmethod
    def _preprocess_mask(mask):
        mask = mask.astype(np.float32) / 255.0
        mask = np.where(mask > 0.5, 1.0, 0.0)
        return mask

    def _read_split(self):
        split_percentage = 10
        filenames = [image.replace(".png", "") for image in os.listdir(self.images_directory)]
        num_to_select = int(len(filenames) * split_percentage / 100)
        val_filenames = random.sample(filenames, num_to_select)
        train_filenames = [filename for filename in filenames if filename not in val_filenames]
        if self.mode == "train":  # 90% for train
            return train_filenames
        elif self.mode == "val":  # 10% for validation
            return val_filenames
        return filenames
    

class SimpleWaterBodiesDataset(WaterBodiesDataset):
    def __getitem__(self, *args, **kwargs):
        sample = super().__getitem__(*args, **kwargs)

        image = Image.fromarray(sample["image"].astype(np.uint8))
        mask = Image.fromarray(sample["mask"].astype(np.uint8))
        if image.size != (512, 512):
            image = image.resize((512, 512), Image.BILINEAR)
        if mask.size != (512, 512):
            mask = mask.resize((512, 512), Image.NEAREST)
        
        image = np.array(image, dtype=np.uint8)
        mask = np.array(mask, dtype=np.uint8)

        if self.transform is not None:
            transformed = self.transform(image=image, mask=mask)
            image = transformed["image"]
            mask = transformed["mask"]

        sample = {
            "image": image, #np.transpose(image, (2, 0, 1)),
            "mask": np.expand_dims(mask, 0)
        }
        return sample

class PredictionWaterBodiesDataset:
    def __init__(self, root, transform=None):
        self.root = root
        self.transform = transform

        self.images_directory = os.path.join(self.root, f"trainset/images")
        self.filenames = self._read_split()  # read train/valid/test splits

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, idx):

        filename = self.filenames[idx]
        image_path = os.path.join(self.images_directory, filename + ".png")

        image = np.array(Image.open(image_path).convert("RGB"))
        image = Image.fromarray(image.astype(np.uint8))
        if image.size != (512, 512):
            print(f"found image with size: {image.size}")
            image = image.resize((512, 512), Image.BILINEAR)
            
        image = np.array(image, dtype=np.uint8)
            
        if self.transform is not None:
            transformed = self.transform(image=image)
            image = transformed["image"]

        
        return filename, image


    def _read_split(self):
        filenames = [image.replace(".png", "") for image in os.listdir(self.images_directory)]
        return filenames