
import os
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 24})


def process_log_files(paths):

    data = {}
    for fpath in paths:
        df = pd.read_csv(fpath, header=None, names=[
                         'Requests', 'Threads', 'Question Number', 'Latency', 'ThroughPut'])

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Latency'].idxmax())
                group = group.drop(group['Latency'].idxmin())
            return group

        grouped = df.groupby(['Threads', 'Question Number']).apply(
            remove_extremes).reset_index(drop=True)

        avg_latency = grouped.groupby(
            ['Threads', 'Question Number']).mean().reset_index()
        avg_latency['Latency'] = avg_latency['Latency']/1000

        data[fpath] = avg_latency

    return data

log_file_paths = ['/root/workspace/deploy/perfcal/perfcal/shell/log/hw/perfcal/overview.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/hw/pgo/overview.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/hw/manual/overview.log']

grouped_data = process_log_files(log_file_paths)

if not os.path.exists('data/csv/HWLatencyBarChart'):
    os.makedirs('data/csv/HWLatencyBarChart')
grouped_data['/root/workspace/deploy/perfcal/perfcal/shell/log/hw/perfcal/overview.log'].to_csv(
    'data/csv/HWLatencyBarChart/perfcal.csv')
grouped_data['/root/workspace/deploy/perfcal/perfcal/shell/log/hw/pgo/overview.log'].to_csv(
    'data/csv/HWLatencyBarChart/pgo.csv')
grouped_data['/root/workspace/deploy/perfcal/perfcal/shell/log/hw/manual/overview.log'].to_csv(
    'data/csv/HWLatencyBarChart/manual.csv')

plt.figure(figsize=(12, 6))

colors = ['blue', 'green']
labels = ['PerfCal-Edu', 'PGo-Edu', 'Manual-Edu']

allHatch = ['/', '-', '*', '\\', '+', 'o', 'O', '.',
            '**', 'OO', 'oo', 'xx', '++', '||', '\\', '//']
cmap = plt.get_cmap("tab10")

allColor = cmap(range(10))

config_labels = []

for i, (path, df) in enumerate(grouped_data.items()):
    config_label = df.apply(
        lambda row: f'{int(row["Threads"])}-{int(row["Question Number"])}', axis=1)
    config_labels.append(config_label)
    plt.bar(df.index + 0.25*i, df['Latency'],
            color=allColor[i], width=0.25, label=labels[i])

plt.xlabel('Number of Clients - Number of Questions', fontsize=30)
plt.ylabel('Latency (ms)', fontsize=30)

plt.xticks(range(len(config_labels[0])), labels=config_labels[0], rotation=45)

plt.legend(loc='upper center', bbox_to_anchor=(
    0.43, 1.3), ncol=3, frameon=False, fontsize=30)
plt.yscale("log")

plt.tight_layout()

plt.subplots_adjust(top=0.85, bottom=0.35, left=0.15, right=0.98)

plt.savefig('data/HWLatency.pdf', dpi=300)

plt.show()
