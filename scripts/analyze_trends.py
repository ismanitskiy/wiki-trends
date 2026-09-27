# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "numpy",
# ]
# ///

import argparse
import json
import os
import sys

import numpy as np


def load_data(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error loading {filepath}: {e}\n")
        return None

def calculate_linear_trend(views):
    if len(views) < 2:
        return {"direction": "stable", "slope_per_month": 0.0, "change_percent_total": 0.0, "r_squared": 0.0, "confidence": "low", "confidence_explanation": "Not enough data points for trend analysis."}
    
    x = np.arange(len(views))
    y = np.array(views)
    
    slope, intercept = np.polyfit(x, y, 1)
    
    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    start_val = y_pred[0]
    end_val = y_pred[-1]
    change_percent = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0
    
    direction = "stable"
    if slope > 0 and change_percent > 5:
        direction = "growing"
    elif slope < 0 and change_percent < -5:
        direction = "declining"
        
    n_points = len(views)
    
    if r_squared > 0.7 and n_points > 24:
        confidence = "висока"
        expl = f"Високий R² ({r_squared:.2f}) на {n_points} точках вказує на стійкий та надійний тренд."
    elif r_squared > 0.4 or n_points > 12:
        confidence = "середня"
        expl = f"Помірний R² ({r_squared:.2f}) на {n_points} точках вказує на помітний тренд із коливаннями."
    else:
        confidence = "низька"
        expl = f"Низький R² ({r_squared:.2f}) або недостатньо даних ({n_points}) свідчить про слабку надійність тренду."
        
    return {
        "direction": direction,
        "slope_per_month": round(slope, 2),
        "change_percent_total": round(change_percent, 2),
        "r_squared": round(r_squared, 2),
        "confidence": confidence,
        "confidence_explanation": expl
    }

def calculate_yoy(data_list):
    yearly_totals = {}
    for item in data_list:
        try:
            year = item['timestamp'].split('-')[0]
            yearly_totals[year] = yearly_totals.get(year, 0) + item['views']
        except:
            pass
            
    years = sorted(list(yearly_totals.keys()))
    yoy_changes = []
    
    for i in range(1, len(years)):
        prev_yr, curr_yr = years[i-1], years[i]
        prev_val, curr_val = yearly_totals[prev_yr], yearly_totals[curr_yr]
        
        if prev_val > 0:
            change = (curr_val - prev_val) / prev_val * 100
            yoy_changes.append({
                "period": f"{curr_yr} vs {prev_yr}",
                "change_percent": round(change, 2)
            })
            
    return yoy_changes

def detect_seasonality(data_list):
    months = {}
    for item in data_list:
        try:
            ts = item['timestamp']
            if len(ts) >= 7 and '-' in ts:
                month = int(ts.split('-')[1])
                if month not in months:
                    months[month] = []
                months[month].append(item['views'])
        except:
            pass
            
    if not months or len(months) < 12:
        return {"detected": False}
        
    avg_by_month = {m: np.mean(v) for m, v in months.items() if len(v) >= 1}
    if not avg_by_month:
         return {"detected": False}
         
    overall_mean = np.mean(list(avg_by_month.values()))
    
    if overall_mean == 0:
        return {"detected": False}
        
    peaks = []
    troughs = []
    
    for m, avg in avg_by_month.items():
        if avg > overall_mean * 1.15:
            peaks.append(m)
        elif avg < overall_mean * 0.85:
            troughs.append(m)
            
    detected = len(peaks) > 0 or len(troughs) > 0
    
    if detected:
        expl = "Виявлено суттєві сезонні коливання інтересу між місяцями."
    else:
        expl = "Вираженої сезонності не виявлено."
        
    return {
        "detected": detected,
        "peak_months": peaks,
        "trough_months": troughs,
        "explanation": expl
    }

def detect_anomalies(data_list):
    views = [d['views'] for d in data_list]
    if len(views) < 3:
        return []
        
    mean = np.mean(views)
    std = np.std(views)
    
    if std == 0:
        return []
        
    anomalies = []
    for item in data_list:
        v = item['views']
        z = (v - mean) / std
        if abs(z) > 2.5:
            anomalies.append({
                "timestamp": item['timestamp'],
                "views": v,
                "expected": round(mean, 2),
                "z_score": round(z, 2),
                "type": "сплеск" if z > 0 else "провал"
            })
            
    return anomalies

def analyze_dataset(data):
    if not data or 'data' not in data:
        return None
        
    data_list = data['data']
    views = [item['views'] for item in data_list]
    
    if not views:
        return None
        
    total_views = sum(views)
    avg_views = np.mean(views)
    median_views = np.median(views)
    
    trend = calculate_linear_trend(views)
    yoy = calculate_yoy(data_list)
    anomalies = detect_anomalies(data_list)
    seasonality = detect_seasonality(data_list)
    
    start_date = data_list[0].get('timestamp', '') if data_list else ''
    end_date = data_list[-1].get('timestamp', '') if data_list else ''

    return {
        "project": data.get("project", ""),
        "article": data.get("article", ""),
        "article_display": data.get("article_display", data.get("article", "")),
        "start_date": start_date,
        "end_date": end_date,
        "data_points": len(data_list),
        "total_views": int(total_views),
        "avg_views": round(float(avg_views), 2),
        "median_views": round(float(median_views), 2),
        "trend": trend,
        "yoy_changes": yoy,
        "anomalies": anomalies,
        "seasonality": seasonality
    }

def compare_datasets(results):
    if len(results) < 2:
        return None
        
    fastest_growth_rate = -float('inf')
    fastest_growing = None
    
    largest_avg_views = -1
    largest_audience = None
    
    for res in results:
        # Normalized growth rate
        avg = res['avg_views']
        slope = res['trend']['slope_per_month']
        norm_growth = (slope / avg) if avg > 0 else 0
        
        if norm_growth > fastest_growth_rate:
            fastest_growth_rate = norm_growth
            fastest_growing = {
                "project": res['project'],
                "normalized_growth_rate": round(norm_growth, 4)
            }
            
        if avg > largest_avg_views:
            largest_avg_views = avg
            largest_audience = {
                "project": res['project'],
                "avg_monthly_views": avg
            }
            
    rec = f"Найшвидше відносне зростання показує {fastest_growing['project']}. Найбільшу загальну аудиторію має {largest_audience['project']}."
    
    return {
        "fastest_growing": fastest_growing,
        "largest_audience": largest_audience,
        "recommendation": rec
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze Wikipedia pageview time-series data.")
    parser.add_argument('--input', type=str, action='append', required=True, help='Path to JSON file(s) from fetch_pageviews.py')
    parser.add_argument('--output', type=str, help='Output file path (default: stdout)')
    
    args = parser.parse_args()
    
    datasets = []
    for filepath in args.input:
        data = load_data(filepath)
        if data:
            result = analyze_dataset(data)
            if result:
                datasets.append(result)
                
    if not datasets:
        sys.stderr.write("No valid datasets processed.\n")
        sys.exit(1)
        
    output = {
        "datasets": datasets,
        "limitations": [
            "Перегляди сторінок Вікіпедії відображають інформаційний інтерес, а не пряму готовність платити за продукт.",
            "На перегляди можуть суттєво впливати зовнішні медійні події, створюючи тимчасові неорганічні сплески.",
            "Менші мовні розділи Вікіпедії мають вищу статистичну волатильність через менший обсяг вибірки.",
            "Трафік ботів відфільтровано (agent=user), проте частина автоматизованих переглядів може залишатися."
        ]
    }
    
    if len(datasets) > 1:
        comp = compare_datasets(datasets)
        if comp:
            output["comparison"] = comp
            
    output_json = json.dumps(output, indent=2, ensure_ascii=False)
    
    if args.output:
        try:
            # create parent dirs if needed
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, 'w') as f:
                f.write(output_json)
        except Exception as e:
            sys.stderr.write(f"Error writing to output file: {e}\n")
            sys.exit(1)
    else:
        print(output_json)

if __name__ == "__main__":
    main()
