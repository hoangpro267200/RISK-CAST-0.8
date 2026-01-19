#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check if loss distribution data is available in backend response
"""
import requests
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_backend_response():
    """Test /results/data endpoint for loss distribution data"""
    try:
        print("=" * 60)
        print("Testing Backend Response for Loss Distribution")
        print("=" * 60)
        
        # Fetch data from backend
        response = requests.get('http://127.0.0.1:8000/results/data', timeout=5)
        
        if response.status_code != 200:
            print(f"[ERROR] Server returned status {response.status_code}")
            return False
        
        data = response.json()
        
        print(f"\n[OK] Server response OK (status {response.status_code})")
        print(f"📦 Response keys: {list(data.keys())[:15]}")
        
        # Check for loss data
        has_loss = 'loss' in data
        has_loss_dist = 'loss_distribution' in data
        has_dist_shapes = 'distribution_shapes' in data
        has_financial_dist = 'financial_distribution' in data
        
        print(f"\n📊 Loss Data Availability:")
        print(f"  - 'loss' field: {'[OK]' if has_loss else '[MISSING]'}")
        print(f"  - 'loss_distribution' field: {'[OK]' if has_loss_dist else '[MISSING]'}")
        print(f"  - 'distribution_shapes' field: {'[OK]' if has_dist_shapes else '[MISSING]'}")
        print(f"  - 'financial_distribution' field: {'[OK]' if has_financial_dist else '[MISSING]'}")
        
        # Check loss metrics
        if has_loss:
            loss = data['loss']
            print(f"\n💰 Loss Metrics:")
            print(f"  - p95: {loss.get('p95', 'N/A')}")
            print(f"  - p99: {loss.get('p99', 'N/A')}")
            print(f"  - expectedLoss: {loss.get('expectedLoss', 'N/A')}")
            print(f"  - Loss keys: {list(loss.keys())}")
        
        # Check loss_distribution
        if has_loss_dist:
            loss_dist = data['loss_distribution']
            if isinstance(loss_dist, list):
                print(f"\n📈 Loss Distribution Array:")
                print(f"  - Length: {len(loss_dist)}")
                print(f"  - First 5 values: {loss_dist[:5]}")
            else:
                print(f"\n[WARNING] loss_distribution is not an array: {type(loss_dist)}")
        
        # Check distribution_shapes
        if has_dist_shapes:
            dist_shapes = data['distribution_shapes']
            print(f"\n📊 Distribution Shapes:")
            print(f"  - Keys: {list(dist_shapes.keys())}")
            if 'loss_histogram' in dist_shapes:
                hist = dist_shapes['loss_histogram']
                print(f"  - loss_histogram keys: {list(hist.keys()) if isinstance(hist, dict) else 'N/A'}")
                if isinstance(hist, dict):
                    if 'bin_centers' in hist:
                        print(f"  - bin_centers length: {len(hist['bin_centers'])}")
                        print(f"  - bin_centers sample: {hist['bin_centers'][:5]}")
                    if 'counts' in hist:
                        print(f"  - counts length: {len(hist['counts'])}")
                        print(f"  - counts sample: {hist['counts'][:5]}")
        
        # Check financial_distribution
        if has_financial_dist:
            fin_dist = data['financial_distribution']
            print(f"\n💵 Financial Distribution:")
            print(f"  - Keys: {list(fin_dist.keys()) if isinstance(fin_dist, dict) else 'N/A'}")
            if isinstance(fin_dist, dict) and 'distribution' in fin_dist:
                dist = fin_dist['distribution']
                if isinstance(dist, list):
                    print(f"  - distribution length: {len(dist)}")
                    print(f"  - distribution sample: {dist[:5]}")
        
        # Summary
        print(f"\n{'=' * 60}")
        print("SUMMARY:")
        print(f"{'=' * 60}")
        
        if has_loss and data['loss']:
            loss = data['loss']
            has_metrics = any([
                loss.get('p95', 0) > 0,
                loss.get('p99', 0) > 0,
                loss.get('expectedLoss', 0) > 0
            ])
            
            if has_metrics:
                print("[OK] Loss metrics are available")
                if has_loss_dist or has_dist_shapes or has_financial_dist:
                    print("[OK] Loss distribution data is available")
                    print("[OK] Frontend should be able to generate lossCurve")
                else:
                    print("[WARNING] Loss distribution data NOT available")
                    print("[WARNING] Frontend will generate synthetic curve from metrics")
            else:
                print("[ERROR] Loss metrics are zero or missing")
        else:
            print("[ERROR] No loss data in response")
        
        print(f"{'=' * 60}\n")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server at http://127.0.0.1:8000")
        print("   Make sure the server is running!")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backend_response()
    sys.exit(0 if success else 1)
