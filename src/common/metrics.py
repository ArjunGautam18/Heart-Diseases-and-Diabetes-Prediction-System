"""Classification metrics and the evaluation plots shared by all model scripts."""
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, matthews_corrcoef
)

ROC_COLOR = "#1D9E75"
PR_COLOR = "#4f90f7"


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "auc": roc_auc_score(y_true, y_proba),
        "pr_auc": average_precision_score(y_true, y_proba),
        "mcc": matthews_corrcoef(y_true, y_pred),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def print_metrics(metrics):
    cm = metrics["confusion_matrix"]
    print(f"  {'Metric':<20} {'Value':>10}")
    print(f"  {'Accuracy':<20} {metrics['accuracy']*100:>9.2f}%")
    print(f"  {'Precision':<20} {metrics['precision']*100:>9.2f}%")
    print(f"  {'Recall':<20} {metrics['recall']*100:>9.2f}%")
    print(f"  {'F1 Score':<20} {metrics['f1']:>10.4f}")
    print(f"  {'ROC-AUC':<20} {metrics['auc']:>10.4f}")
    print(f"  {'PR-AUC':<20} {metrics['pr_auc']:>10.4f}")
    print(f"  {'MCC':<20} {metrics['mcc']:>10.4f}")
    print(f"\n  TP={cm['tp']}  TN={cm['tn']}  FP={cm['fp']}  FN={cm['fn']}")


def save_evaluation_panel(y_true, y_proba, metrics, model_name, disease_label,
                          class_labels, output_paths, cm_subtitle=None,
                          precision_target=None, dpi=130):
    """Confusion matrix + ROC + precision-recall panel, written to every output path."""
    cm = metrics["confusion_matrix"]
    matrix = [[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    fig.suptitle(
        f"{disease_label} — {model_name} | "
        f"Prec={metrics['precision']*100:.1f}%  Rec={metrics['recall']*100:.1f}%  "
        f"F1={metrics['f1']:.3f}  AUC={metrics['auc']:.3f}",
        fontsize=11, fontweight="bold"
    )

    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", ax=axes[0],
                xticklabels=class_labels, yticklabels=class_labels)
    subtitle = cm_subtitle or f"TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']}"
    axes[0].set_title(f"Confusion Matrix\n{subtitle}")
    axes[0].set_ylabel("Actual"); axes[0].set_xlabel("Predicted")

    fpr, tpr, _ = roc_curve(y_true, y_proba)
    axes[1].plot(fpr, tpr, color=ROC_COLOR, lw=2, label=f"AUC={metrics['auc']:.3f}")
    axes[1].plot([0, 1], [0, 1], "--", color="gray")
    axes[1].fill_between(fpr, tpr, alpha=0.08, color=ROC_COLOR)
    axes[1].set_xlabel("False Positive Rate"); axes[1].set_ylabel("True Positive Rate")
    axes[1].set_title("ROC Curve"); axes[1].legend()

    prec_curve, rec_curve, _ = precision_recall_curve(y_true, y_proba)
    axes[2].plot(rec_curve, prec_curve, color=PR_COLOR, lw=2, label=f"PR-AUC={metrics['pr_auc']:.3f}")
    axes[2].axhline(y=y_true.mean(), linestyle="--", color="gray", label="Baseline")
    if precision_target is not None:
        axes[2].axhline(y=precision_target, linestyle=":", color="#f5a623",
                        label=f"{precision_target*100:.0f}% precision target")
    axes[2].fill_between(rec_curve, prec_curve, alpha=0.08, color=PR_COLOR)
    axes[2].set_xlabel("Recall"); axes[2].set_ylabel("Precision")
    axes[2].set_title("Precision-Recall Curve"); axes[2].legend(fontsize=8)

    plt.tight_layout()
    for path in output_paths:
        plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()


def save_roc_curve(y_true, y_proba, auc, title, output_path, dpi=130):
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    plt.figure(figsize=(5, 4))
    plt.plot(fpr, tpr, color=ROC_COLOR, lw=2, label=f"AUC = {auc:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate")
    plt.title(title); plt.legend(); plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
