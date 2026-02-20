#!/usr/bin/env python3
"""
Test script to verify Loki connectivity and label visibility.
Run this with USE_GRAFANA=1 to test the logging setup.
"""

import os
import sys
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Simulation_Frame.newprint import NewPrint

def main():
    print("=" * 60)
    print("Loki Connection Test")
    print("=" * 60)
    
    # Test 1: Check if USE_GRAFANA is set
    use_grafana = os.environ.get("USE_GRAFANA")
    print(f"\n1. USE_GRAFANA environment variable: {use_grafana}")
    if not use_grafana:
        print("   ⚠️  Warning: USE_GRAFANA not set. Logs will only print to console.")
        print("   Set it with: export USE_GRAFANA=1")
    
    # Test 2: Test Loki connection
    print("\n2. Testing Loki connection...")
    NewPrint.test_loki_connection()
    
    # Test 3: Send test logs with different labels
    if use_grafana:
        print("\n3. Sending test log entries...")
        test_printer = NewPrint("test_consumer")
        
        # Send logs with different label combinations
        test_printer.newprint("Test message 1", level="info", event="test")
        time.sleep(0.1)
        test_printer.newprint("Test message 2", level="warning", event="test")
        time.sleep(0.1)
        test_printer.newprint("Test message 3", level="error", event="production")
        
        print("\n   ✓ Test logs sent. Check Grafana Explore in a few seconds.")
        print("\n   In Grafana Explore:")
        print("   - Select your Loki datasource")
        print("   - Use LogQL query: {job=\"consumer\"}")
        print("   - Or browse labels using the label selector dropdown")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
