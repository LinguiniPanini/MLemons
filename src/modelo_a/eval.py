import argparse
import os

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    balanced_accuracy_score,
)

from src.modelo_a.dataset import build_datasets, CLASSES
from src.modelo_a.transforms import eval_transform
from src.modelo_a.script import build_model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/lemons")
    parser.add_argument("--model", type=str, default="models/modelo_a.pth")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--num_workers", type=int, default=2)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _, _, test_ds = build_datasets(args.data, eval_transform=eval_transform())
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                             num_workers=args.num_workers)
    print(f"Test set: {len(test_ds)} muestras")

    # cargar modelo (estructura igual que en training; pesos del checkpoint)
    model = build_model(freeze_backbone=False).to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()

    y_true = []
    y_pred = []
    with torch.no_grad():
        for imgs, labels in test_loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            preds = outputs.argmax(dim=1).cpu().tolist()
            y_pred.extend(preds)
            y_true.extend(labels.tolist())

    bal_acc = balanced_accuracy_score(y_true, y_pred)
    print(f"Test balanced accuracy: {bal_acc:.4f}")
    print()
    print("Classification report:")
    print(classification_report(y_true, y_pred, target_names=CLASSES, digits=4))
    print("Confusion matrix (filas=actual, columnas=predicho):")
    cm = confusion_matrix(y_true, y_pred)
    print(f"            {CLASSES[0]:>15} {CLASSES[1]:>15}")
    for i, row in enumerate(cm):
        print(f"{CLASSES[i]:>10} {row[0]:>15} {row[1]:>15}")
