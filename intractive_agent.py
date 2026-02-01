#!/usr/bin/env python3
"""
Interactive Global Stock Research Agent - 100% FREE VERSION
Analyze stocks from any exchange worldwide - NO OpenAI required!
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from free_stock_agent import research_agent, print_report
import sys


def print_welcome():
    """Print welcome message with examples"""
    print("\n" + "="*70)
    print("🌍 GLOBAL STOCK RESEARCH AGENT - 100% FREE")
    print("="*70)
    print("\n✨ Analyze stocks from ANY exchange worldwide - No payment needed!")
    print("💰 Completely FREE - No OpenAI API required!")
    print("\n📋 Examples:")
    print("   • US: Apple, Microsoft, Tesla, NVDA")
    print("   • India: TCS, Reliance, Infosys, Wipro")
    print("   • UK: BP, Shell, HSBC, Vodafone")
    print("   • Japan: Toyota, Sony, Nintendo")
    print("   • Europe: Volkswagen, SAP, Nestle")
    print("   • China: Tencent, Alibaba")
    print("\n💡 Just type the company name or ticker symbol!")
    print("   Type 'quit' or 'exit' to stop\n")
    print("="*70 + "\n")


def get_stock_input():
    """Get stock symbol/name from user"""
    try:
        user_input = input("🔍 Enter company name or ticker: ").strip()
        return user_input
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")
        sys.exit(0)


def interactive_mode():
    """Run the agent in interactive mode"""
    print_welcome()
    
    while True:
        # Get user input
        stock_input = get_stock_input()
        
        # Check for exit commands
        if stock_input.lower() in ['quit', 'exit', 'q', '']:
            print("\n👋 Thanks for using Global Stock Research Agent!")
            break
        
        # Analyze the stock
        print(f"\n🔄 Analyzing '{stock_input}'...\n")
        result = research_agent(stock_input)
        
        if result:
            print_report(result)
        else:
            print(f"\n❌ Could not analyze '{stock_input}'")
            print("\n💡 Suggestions:")
            print("   • Try the full company name")
            print("   • Use the exact ticker symbol")
            print("   • For non-US stocks, try adding country (e.g., 'Tata Motors India')")
            print()
        
        # Ask if they want to continue
        try:
            continue_input = input("🔄 Analyze another stock? (y/n): ").strip().lower()
            if continue_input in ['n', 'no']:
                print("\n👋 Thanks for using Global Stock Research Agent!")
                break
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break


def single_stock_mode(stock_name):
    """Analyze a single stock from command line argument"""
    print(f"\n🔄 Analyzing '{stock_name}'...\n")
    result = research_agent(stock_name)
    
    if result:
        print_report(result)
    else:
        print(f"\n❌ Could not analyze '{stock_name}'")
        print("\n💡 Try running in interactive mode: python free_interactive.py")


def main():
    """Main entry point"""
    # Check if stock name provided as argument
    if len(sys.argv) > 1:
        stock_name = " ".join(sys.argv[1:])
        single_stock_mode(stock_name)
    else:
        interactive_mode()


if __name__ == "__main__":
    # Verify NEWS API key (optional but helpful)
    if not os.getenv("NEWS_API_KEY"):
        print("\n⚠️  NOTE: NEWS_API_KEY not found in .env file")
        print("   The agent will work but sentiment analysis will be limited.")
        print("   You can still get BUY/SELL/HOLD based on price data!\n")
    
    print("\n💰 100% FREE VERSION - No OpenAI charges!")
    print("   All explanations generated locally - zero cost!\n")
    
    main()
