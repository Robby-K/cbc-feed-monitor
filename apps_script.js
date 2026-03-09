/**
 * Google Apps Script — paste this into your spreadsheet's script editor.
 *
 * Setup:
 * 1. Open the Google Sheet
 * 2. Extensions > Apps Script
 * 3. Delete any existing code, paste this entire file
 * 4. Update GITHUB_CSV_URL below with your repo's raw URL
 * 5. Click Run on "test" to authorize permissions
 * 6. Go to Triggers (clock icon on left sidebar)
 * 7. Click "+ Add Trigger"
 *    - Function: importLatestCSV
 *    - Event source: Time-driven
 *    - Type: Week timer
 *    - Day: Friday
 *    - Time: 9am to 10am
 * 8. Save
 */

// UPDATE THIS with your GitHub repo's raw URL for latest.csv
var GITHUB_CSV_URL = "https://raw.githubusercontent.com/OWNER/cbc-feed-monitor/main/results/latest.csv";

function importLatestCSV() {
  var response = UrlFetchApp.fetch(GITHUB_CSV_URL);
  var csvText = response.getContentText();
  var data = Utilities.parseCsv(csvText);

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var tabName = Utilities.formatDate(new Date(), "America/Toronto", "yyyy-MM-dd");

  // Delete existing tab with same name if it exists
  var existing = ss.getSheetByName(tabName);
  if (existing) {
    ss.deleteSheet(existing);
  }

  var sheet = ss.insertSheet(tabName);
  sheet.getRange(1, 1, data.length, data[0].length).setValues(data);

  // Bold header row
  sheet.getRange(1, 1, 1, data[0].length).setFontWeight("bold");

  // Auto-resize columns
  for (var i = 1; i <= data[0].length; i++) {
    sheet.autoResizeColumn(i);
  }

  Logger.log("Created tab '" + tabName + "' with " + (data.length - 1) + " rows");
}

function test() {
  Logger.log(SpreadsheetApp.getActiveSpreadsheet().getName());
  Logger.log("Fetching: " + GITHUB_CSV_URL);
}
