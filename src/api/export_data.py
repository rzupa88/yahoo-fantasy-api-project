from data_storage import DataStorage

def main():
    storage = DataStorage()
    # Export 2025 season data (our current season)
    csv_path = storage.export_to_csv(season=2025)
    print(f"\nData exported to: {csv_path}")
    print("You can now open this file in Excel or any spreadsheet software")

if __name__ == "__main__":
    main()