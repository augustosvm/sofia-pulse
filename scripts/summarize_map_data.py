import json
import pandas as pd

def df_to_markdown(df):
    if df.empty:
        return ""
    # Header
    cols = df.columns
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    # Rows
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(val) for val in row.values) + " |")
    return "\n".join([header, sep] + rows)

def summarize():
    try:
        with open("map_data_dump.json", "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: map_data_dump.json not found. Run extraction first.")
        return
    
    md_output = ["# Sofia Map Data APIs Extraction\n"]
    md_output.append(f"Generated at: {pd.Timestamp.now()}\n")

    for name, content in data.items():
        md_output.append(f"## {name}")
        md_output.append(f"- **URL**: `{content.get('url')}`")
        md_output.append(f"- **Description**: {content.get('description')}")
        md_output.append(f"- **Status**: {content.get('status')}")
        
        if content.get('status') != 'Success':
            md_output.append(f"- **Error**: {content.get('error')}\n")
            continue
            
        raw_data = content.get('data')
        
        # Determine table structure based on endpoint
        df = None
        if "Capital" in name:
            # Structure: { countries: [...] }
            rows = raw_data.get('countries', [])
            if rows:
                df = pd.DataFrame(rows)
                # Select key columns
                cols = ['country_code', 'total_usd', 'momentum', 'stage', 'confidence', 'flow_type']
                # Ensure cols exist
                cols = [c for c in cols if c in df.columns]
                df = df[cols]
        
        elif "Security Risk" in name:
             # Structure: { countries: [...] }
             rows = raw_data.get('countries', [])
             if rows:
                 df = pd.DataFrame(rows)
                 cols = ['country_code', 'total_risk', 'risk_level', 'coverage_score_global', 'warning']
                 cols = [c for c in cols if c in df.columns]
                 df = df[cols]

        elif "Security Map" in name:
             # Structure: { features: [...] }
             features = raw_data.get('features', [])
             if features:
                 # Flatten properties
                 rows = [f['properties'] for f in features]
                 df = pd.DataFrame(rows)
                 cols = ['countryCode', 'topEventType', 'fatalities', 'severityNorm', 'dataSource']
                 cols = [c for c in cols if c in df.columns]
                 df = df[cols]
        
        if df is not None and not df.empty:
            md_output.append(f"- **Total Records**: {len(df)}")
            md_output.append("\n### Data Sample (Top 20)")
            md_output.append(df_to_markdown(df.head(20)))
            md_output.append("\n")
        else:
            md_output.append("- **No structured data found or empty response.**\n")

    with open("map_data_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_output))
    
    print("Summary written to map_data_summary.md")

if __name__ == "__main__":
    summarize()
