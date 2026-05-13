import os
from PIL import Image
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split

# orden importa: indice = label
CLASSES = ["good_quality", "bad_quality"]  # 0 = sano, 1 = defectuoso


class LemonDataset(Dataset):
    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


def list_samples(root_dir):
    samples = []
    for label, cls in enumerate(CLASSES):
        cls_dir = os.path.join(root_dir, cls)
        for fname in sorted(os.listdir(cls_dir)):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                samples.append((os.path.join(cls_dir, fname), label))
    return samples


def split_samples(samples, val_size=0.15, test_size=0.15, seed=42):
    paths = [s[0] for s in samples]
    labels = [s[1] for s in samples]

    train_paths, temp_paths, train_y, temp_y = train_test_split(
        paths,
        labels,
        test_size=val_size + test_size,
        random_state=seed,
        stratify=labels,
    )

    rel_test = test_size / (val_size + test_size)
    val_paths, test_paths, val_y, test_y = train_test_split(
        temp_paths,
        temp_y,
        test_size=rel_test,
        random_state=seed,
        stratify=temp_y,
    )

    return (
        list(zip(train_paths, train_y)),
        list(zip(val_paths, val_y)),
        list(zip(test_paths, test_y)),
    )


def build_datasets(root_dir, train_transform=None, eval_transform=None):
    samples = list_samples(root_dir)
    train, val, test = split_samples(samples)
    return (
        LemonDataset(train, transform=train_transform),
        LemonDataset(val, transform=eval_transform),
        LemonDataset(test, transform=eval_transform),
    )


if __name__ == "__main__":
    # smoke test: corre `python -m src.modelo_a.dataset data/lemons`
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "data/lemons"
    samples = list_samples(root)
    print(f"Total muestras: {len(samples)}")
    train, val, test = split_samples(samples)
    print(f"train {len(train)} | val {len(val)} | test {len(test)}")
    print(
        f"train balance: {sum(1 for _, y in train if y == 0)} sano / {sum(1 for _, y in train if y == 1)} defectuoso"
    )
