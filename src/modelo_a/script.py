import argparse
import os
import time

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

from src.modelo_a.dataset import build_datasets
from src.modelo_a.transforms import train_transform, eval_transform


def build_model(freeze_backbone):
    weights = MobileNet_V2_Weights.IMAGENET1K_V2
    model = mobilenet_v2(weights=weights)
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
    # cabeza nueva: 1280 features -> 2 clases (sano, defectuoso)
    model.classifier[1] = nn.Linear(model.last_channel, 2)
    return model


def run_epoch(model, loader, criterion, optimizer, device, train_mode):
    if train_mode:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    context = torch.enable_grad() if train_mode else torch.no_grad()
    with context:
        for imgs, labels in loader:
            imgs = imgs.to(device)
            labels = labels.to(device)

            if train_mode:
                optimizer.zero_grad()

            outputs = model(imgs)
            loss = criterion(outputs, labels)

            if train_mode:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * imgs.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += imgs.size(0)

    return total_loss / total, correct / total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--freeze_backbone", action="store_true", default=True)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    # rutas: SageMaker inyecta SM_*; en local pasas --train data/lemons --model-dir models
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "data/lemons"))
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "models"))
    args, _ = parser.parse_known_args()

    torch.manual_seed(args.seed)
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Args: lr={args.lr} batch={args.batch_size} epochs={args.epochs} freeze={args.freeze_backbone}")

    # datasets
    train_ds, val_ds, test_ds = build_datasets(
        args.train,
        train_transform=train_transform(),
        eval_transform=eval_transform(),
    )
    print(f"Datasets: train {len(train_ds)} | val {len(val_ds)} | test {len(test_ds)}")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers, persistent_workers=args.num_workers > 0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            num_workers=args.num_workers, persistent_workers=args.num_workers > 0)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                             num_workers=args.num_workers, persistent_workers=args.num_workers > 0)

    # modelo + optimizador
    model = build_model(args.freeze_backbone).to(device)
    trainable = [p for p in model.parameters() if p.requires_grad]
    print(f"Parametros entrenables: {sum(p.numel() for p in trainable):,}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(trainable, lr=args.lr)

    # training loop
    best_val_acc = 0.0
    os.makedirs(args.model_dir, exist_ok=True)
    model_path = os.path.join(args.model_dir, "modelo_a.pth")

    for epoch in range(args.epochs):
        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer, device, train_mode=True)
        val_loss, val_acc = run_epoch(model, val_loader, criterion, optimizer, device, train_mode=False)
        elapsed = time.time() - t0

        print(f"Epoch {epoch + 1}/{args.epochs} "
              f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} "
              f"time={elapsed:.1f}s")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), model_path)
            print(f"Mejor val_acc, guardado checkpoint en {model_path}")

    # test final con el mejor checkpoint
    model.load_state_dict(torch.load(model_path))
    test_loss, test_acc = run_epoch(model, test_loader, criterion, optimizer, device, train_mode=False)
    print(f"Test loss: {test_loss:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")  # captado por metric_definitions regex
