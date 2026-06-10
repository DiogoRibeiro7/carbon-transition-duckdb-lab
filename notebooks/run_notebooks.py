from pathlib import Path
import pandas as pd

mart_path = Path('data/processed/marts/mart_country_year_transition.csv')
out_dir = Path('reports/sample_run')
out_dir.mkdir(parents=True, exist_ok=True)

print('Reading', mart_path)
df = pd.read_csv(mart_path)
print('Loaded rows:', len(df))

# Numeric summary
num_cols = df.select_dtypes(include='number').columns.tolist()
summary = df[num_cols].describe().transpose()
summary_path = out_dir / 'transition_numeric_summary.csv'
summary.to_csv(summary_path)
print('Wrote numeric summary to', summary_path)

# Markdown report
report_md = out_dir / 'transition_report_from_runner.md'
with report_md.open('w', encoding='utf8') as f:
    f.write('# Transition numeric summary\n\n')
    f.write('Loaded rows: ' + str(len(df)) + '\n\n')
    f.write('Top numeric columns:\n')
    for c in num_cols[:10]:
        f.write('- ' + c + '\n')
print('Wrote markdown report to', report_md)

# Top countries by records
country_col = None
for c in ['country', 'Country', 'location', 'country_name', 'country_name_clean']:
    if c in df.columns:
        country_col = c
        break

if country_col is not None:
    agg = df.groupby(country_col).size().reset_index(name='records')
    agg = agg.sort_values('records', ascending=False).head(50)
    top_path = out_dir / 'top_countries_by_records.csv'
    agg.to_csv(top_path, index=False)
    print('Wrote top countries CSV to', top_path)
else:
    print('No country-like column found; skipping top countries aggregation')

print('Done')
