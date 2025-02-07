from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict

import requests
from prometheus_client.parser import text_string_to_metric_families, MetricFamily
from app.backend.config import METRICS_ENDPOINT


@dataclass
class MetricSample:
    name: str
    labels: Dict[str, str]
    value: float
    timestamp: str | None


def format_value(value: float) -> str:
    if value > 1e9:
        return f"{value:.2e}"
    elif value.is_integer():
        return f"{int(value)}"
    else:
        return f"{value:.3f}"


def query_and_parse_metrics() -> List[MetricFamily]:
    response = requests.get(METRICS_ENDPOINT)
    response.raise_for_status()
    metrics_data: str = response.text
    return list(text_string_to_metric_families(metrics_data))


def group_metrics_by_base_name(metric_families: List[MetricFamily]) -> Dict[str, List[MetricFamily]]:
    grouped_metrics: Dict[str, List[MetricFamily]] = defaultdict(list)
    for family in metric_families:
        base_name = family.name.split('_created')[0].split('_bucket')[0]
        grouped_metrics[base_name].append(family)
    return grouped_metrics


def print_histogram_metrics(family: MetricFamily) -> None:
    print(f"\nГистограмма: {family.name}")
    print(f"Описание: {family.documentation}")
    print("\nРаспределение:")
    print(f"{'Интервал':>15} {'Количество':>12}")
    print("-" * 30)

    buckets = []
    for sample in family.samples:
        if sample[0].endswith('_bucket'):
            le = sample[1].get('le', '')
            count = sample[2]
            buckets.append((le, count))

    prev_count = 0
    for le, count in sorted(buckets, key=lambda x: float(x[0].replace('+Inf', 'inf'))):
        interval_count = count - prev_count
        if le == '+Inf':
            interval = f">{buckets[-2][0]}"
        else:
            interval = f"≤{le}s"
        print(f"{interval:>15} {interval_count:>12.0f}")
        prev_count = count


def print_counter_metrics(family: MetricFamily) -> None:
    print(f"\nСчетчик: {family.name}")
    print(f"Описание: {family.documentation}")
    print("\nЗначения:")
    print(f"{'Метки':>50} {'Значение':>15}")
    print("-" * 70)

    for sample in family.samples:
        labels_str = ", ".join(f"{k}={v}" for k, v in sample[1].items()) if sample[1] else "-"
        value_str = format_value(sample[2])
        print(f"{labels_str:>50} {value_str:>15}")


def print_metrics_table(metric_families: List[MetricFamily]) -> None:
    grouped_metrics = group_metrics_by_base_name(metric_families)

    for base_name, families in grouped_metrics.items():
        print(f"\n{'='*80}")
        print(f"Метрика: {base_name}")
        print('='*80)

        for family in families:
            if family.type == "histogram":
                print_histogram_metrics(family)
            elif family.type == "counter" or family.type == "gauge":
                print_counter_metrics(family)
        print()


def main() -> None:
    try:
        metric_families: List[MetricFamily] = query_and_parse_metrics()
        print_metrics_table(metric_families)
    except Exception as e:
        print(f"Ошибка при получении метрик: {str(e)}")


if __name__ == '__main__':
    main()
