const functions = require('firebase-functions');

const {google} = require('googleapis');

const config = require('./config.json')


async function appendSheetRow (submission) {
  const jwt = new google.auth.JWT(
    config.client_email,
    null,
    config.private_key,
    ['https://www.googleapis.com/auth/spreadsheets']
  )
  
  google.sheets('v4').spreadsheets.values.append(
    {
      spreadsheetId: config.spreadsheet_id,
      auth: jwt,
      valueInputOption: 'RAW',
      range: 'A1',
      resource: { values: [submission] }
    },
    (err, result) => {
      if (err) {
        throw err
      } else {
        console.log('Updated sheet: ' + result.data.updates.updatedRange)
      }
    }
  )

}

//node -e "require('./index.js').runTest()"
exports.runTest = () => {
  let fakeSubmission = ["hello", "world", Date.now()]
  appendSheetRow(fakeSubmission);
}


exports.sendToSheets = functions.https.onCall((data, context) => {
  functions.logger.log("App context:", context.app);

  appendSheetRow(data.submission)
});




