#!/usr/bin/env python3
"""
Plot Viewer and Comparison Tool
图表查看和对比工具

This script helps users view and compare different types of generated plots.
"""

import os
import webbrowser
from pathlib import Path

def list_available_plots():
    """List all available plots in the plots directory"""
    plots_dir = Path("plots")
    if not plots_dir.exists():
        print("❌ No plots directory found!")
        return []
    
    plots = {
        'backtrader_native': [],
        'interactive_dashboards': [], 
        'performance_charts': [],
        'comparison_charts': [],
        'other': []
    }
    
    for plot_file in plots_dir.iterdir():
        if plot_file.is_file():
            file_name = plot_file.name.lower()
            
            if 'backtrader' in file_name and file_name.endswith('.png'):
                plots['backtrader_native'].append(plot_file)
            elif 'dashboard' in file_name and file_name.endswith('.html'):
                plots['interactive_dashboards'].append(plot_file)
            elif 'performance' in file_name:
                plots['performance_charts'].append(plot_file)
            elif 'comparison' in file_name:
                plots['comparison_charts'].append(plot_file)
            else:
                plots['other'].append(plot_file)
    
    return plots

def display_plot_menu():
    """Display an interactive menu for viewing plots"""
    plots = list_available_plots()
    
    if not any(plots.values()):
        print("❌ No plots found! Run some backtests first to generate visualizations.")
        return
    
    print("\n" + "="*60)
    print("📊 BITCOIN STRATEGY VISUALIZATION VIEWER")
    print("="*60)
    
    menu_items = []
    item_count = 1
    
    # Backtrader Native Plots
    if plots['backtrader_native']:
        print(f"\n🔸 BACKTRADER NATIVE PLOTS ({len(plots['backtrader_native'])})")
        print("-" * 40)
        for plot in plots['backtrader_native']:
            menu_items.append(('backtrader', plot))
            print(f"{item_count:2d}. {plot.name}")
            item_count += 1
    
    # Interactive Dashboards
    if plots['interactive_dashboards']:
        print(f"\n🔸 INTERACTIVE DASHBOARDS ({len(plots['interactive_dashboards'])})")
        print("-" * 40)
        for plot in plots['interactive_dashboards']:
            menu_items.append(('dashboard', plot))
            print(f"{item_count:2d}. {plot.name}")
            item_count += 1
    
    # Performance Charts
    if plots['performance_charts']:
        print(f"\n🔸 PERFORMANCE CHARTS ({len(plots['performance_charts'])})")
        print("-" * 40)
        for plot in plots['performance_charts']:
            menu_items.append(('performance', plot))
            print(f"{item_count:2d}. {plot.name}")
            item_count += 1
    
    # Comparison Charts
    if plots['comparison_charts']:
        print(f"\n🔸 STRATEGY COMPARISONS ({len(plots['comparison_charts'])})")
        print("-" * 40)
        for plot in plots['comparison_charts']:
            menu_items.append(('comparison', plot))
            print(f"{item_count:2d}. {plot.name}")
            item_count += 1
    
    # Other Plots
    if plots['other']:
        print(f"\n🔸 OTHER VISUALIZATIONS ({len(plots['other'])})")
        print("-" * 40)
        for plot in plots['other']:
            menu_items.append(('other', plot))
            print(f"{item_count:2d}. {plot.name}")
            item_count += 1
    
    print(f"\n{item_count}. 🔄 Refresh plot list")
    print(f"{item_count+1}. ❌ Exit")
    
    while True:
        try:
            choice = input(f"\nSelect plot to view (1-{item_count+1}): ").strip()
            
            if choice == str(item_count):  # Refresh
                display_plot_menu()
                return
            elif choice == str(item_count + 1):  # Exit
                print("👋 Goodbye!")
                return
            
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(menu_items):
                plot_type, plot_path = menu_items[choice_num]
                view_plot(plot_type, plot_path)
            else:
                print("❌ Invalid choice. Please try again.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return

def view_plot(plot_type, plot_path):
    """View a specific plot based on its type"""
    abs_path = plot_path.resolve()
    
    print(f"\n📊 Opening: {plot_path.name}")
    print(f"   Type: {plot_type.upper()}")
    print(f"   Path: {abs_path}")
    
    if plot_type == 'dashboard' or str(plot_path).endswith('.html'):
        # Open HTML files in browser
        try:
            file_url = f"file://{abs_path}"
            webbrowser.open(file_url)
            print("✅ Interactive dashboard opened in web browser!")
        except Exception as e:
            print(f"❌ Error opening in browser: {e}")
            print(f"💡 You can manually open: {abs_path}")
    
    elif str(plot_path).endswith('.png'):
        # For PNG files, provide instructions to view
        print("📷 PNG image file - please open with your preferred image viewer.")
        print(f"💡 File location: {abs_path}")
        
        # On macOS, try to open with default viewer
        try:
            os.system(f"open '{abs_path}'")
            print("✅ Image opened with default viewer!")
        except:
            print("💡 Please open the file manually with your image viewer.")
    
    else:
        print("📄 Unknown file type - please open manually.")
        print(f"💡 File location: {abs_path}")

def show_plot_summary():
    """Show a summary of all available plots"""
    plots = list_available_plots()
    
    print("\n" + "="*60)
    print("📊 PLOT SUMMARY")
    print("="*60)
    
    total_plots = sum(len(plot_list) for plot_list in plots.values())
    
    if total_plots == 0:
        print("❌ No plots found!")
        print("💡 Run 'python quick_test.py --save-plots' or 'python strategy_tester.py --save-plots' to generate visualizations.")
        return
    
    print(f"📈 Total Plots: {total_plots}")
    print()
    
    for category, plot_list in plots.items():
        if plot_list:
            category_name = category.replace('_', ' ').title()
            print(f"🔸 {category_name}: {len(plot_list)} files")
            for plot in plot_list[:3]:  # Show first 3 files
                print(f"   - {plot.name}")
            if len(plot_list) > 3:
                print(f"   ... and {len(plot_list) - 3} more")
            print()
    
    print("💡 Use 'python view_plots.py' to open and view individual plots.")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        show_plot_summary()
    else:
        display_plot_menu()

if __name__ == '__main__':
    main()