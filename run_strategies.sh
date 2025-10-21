#!/bin/bash
# 比特币策略回测便捷脚本
# Bitcoin Strategy Backtesting Convenience Script

echo "==================================="
echo "     比特币策略回测系统"
echo "   Bitcoin Strategy Tester"
echo "==================================="
echo

# Function to show menu
show_menu() {
    echo "请选择操作 (Choose an option):"
    echo "1. 快速测试 (Quick test - Top 3 strategies on Bitcoin 2020-2024)"
    echo "2. 全策略测试 (All strategies test - Bitcoin 2020-2024)"
    echo "3. 自定义时间测试 (Custom time period test)"
    echo "4. 查看可用策略 (List available strategies)"
    echo "5. 单策略测试 (Single strategy test)"
    echo "6. 长期测试 (Long-term test - Bitcoin 2017-2024)"
    echo "7. 可视化测试 (Visual test with charts)"
    echo "8. 分析已保存结果 (Analyze saved results)"
    echo "0. 退出 (Exit)"
    echo
}

# Main menu loop
while true; do
    show_menu
    read -p "请输入选择 (Enter choice): " choice
    echo
    
    case $choice in
        1)
            echo "🚀 运行快速测试..."
            python quick_test.py
            ;;
        2)
            echo "🚀 运行全策略测试 (2020-2024)..."
            python strategy_tester.py --strategy all --start 2020-01-01 --end 2024-01-01
            ;;
        3)
            echo "📝 自定义时间测试设置:"
            read -p "输入策略名称 (Strategy name, 默认 all): " strategy
            strategy=${strategy:-all}
            
            read -p "输入开始日期 (Start date, 默认 2020-01-01): " start
            start=${start:-2020-01-01}
            
            read -p "输入结束日期 (End date, 默认 2024-01-01): " end
            end=${end:-2024-01-01}
            
            echo "🚀 运行比特币自定义测试: $strategy from $start to $end"
            python strategy_tester.py --strategy $strategy --start $start --end $end
            ;;
        4)
            echo "📋 可用策略列表:"
            python strategy_tester.py --list-strategies
            ;;
        5)
            echo "📝 单策略测试设置:"
            read -p "输入策略名称 (Strategy name): " strategy
            if [ -z "$strategy" ]; then
                echo "❌ 策略名称不能为空"
                continue
            fi
            
            echo "🚀 测试单个策略: $strategy"
            python strategy_tester.py --strategy $strategy --start 2020-01-01 --end 2024-01-01
            ;;
        6)
            echo "🚀 运行长期测试 (2017-2024)..."
            python strategy_tester.py --strategy all --start 2017-01-01 --end 2024-01-01
            ;;
        7)
            echo "📊 可视化测试选项:"
            echo "a. 快速可视化测试 (Quick test with plots)"
            echo "b. 全策略可视化测试 (All strategies with plots)"
            echo "c. 单策略可视化 (Single strategy with plots)"
            read -p "选择子选项 (Choose sub-option): " visual_choice
            
            case $visual_choice in
                a)
                    echo "🚀 运行快速可视化测试..."
                    python quick_test.py --plot --save-plots
                    ;;
                b)
                    echo "🚀 运行全策略可视化测试..."
                    python strategy_tester.py --strategy all --start 2020-01-01 --end 2024-01-01 --plot --save-plots
                    ;;
                c)
                    read -p "输入策略名称 (Strategy name): " strategy
                    if [ -z "$strategy" ]; then
                        echo "❌ 策略名称不能为空"
                        continue
                    fi
                    echo "🚀 运行单策略可视化: $strategy"
                    python strategy_tester.py --strategy $strategy --start 2020-01-01 --end 2024-01-01 --plot --save-plots
                    ;;
                *)
                    echo "❌ 无效的子选项"
                    ;;
            esac
            ;;
        8)
            echo "📈 分析已保存结果:"
            echo "a. 分析最新结果 (Analyze latest results)"
            echo "b. 交互式分析 (Interactive analysis)"
            echo "c. 指定文件分析 (Analyze specific file)"
            read -p "选择子选项 (Choose sub-option): " analysis_choice
            
            case $analysis_choice in
                a)
                    echo "🚀 分析最新结果..."
                    python plot_results.py --latest --save-plots
                    ;;
                b)
                    echo "🚀 启动交互式分析..."
                    python plot_results.py --latest --interactive
                    ;;
                c)
                    read -p "输入结果文件路径 (Results file path): " file_path
                    if [ -z "$file_path" ]; then
                        echo "❌ 文件路径不能为空"
                        continue
                    fi
                    echo "🚀 分析指定文件: $file_path"
                    python plot_results.py "$file_path" --save-plots
                    ;;
                *)
                    echo "❌ 无效的子选项"
                    ;;
            esac
            ;;
        0)
            echo "👋 再见!"
            break
            ;;
        *)
            echo "❌ 无效选择，请重新输入"
            ;;
    esac
    
    echo
    read -p "按回车键继续... (Press Enter to continue...)"
    echo
done