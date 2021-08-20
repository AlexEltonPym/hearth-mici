const functions = require('firebase-functions');
const { google } = require('googleapis');

const config = require('./config.json')


exports.sendToSheets = functions.https.onCall((data, context) => {
  functions.logger.log("App context: ", context.app);
  const jwt = new google.auth.JWT(
    config.client_email,
    null,
    config.private_key,
    ['https://www.googleapis.com/auth/spreadsheets']
  )


  let vals = data.submissions.map((sub) => {
    let asArr = Object.entries(sub[1]);
    return [].concat(...asArr); //flat not supported yet
  })

  const request = {
    spreadsheetId: config.spreadsheet_id,
    auth: jwt,
    valueInputOption: 'RAW',
    range: 'A1:A10000',
    resource: { values: vals }
  };

  const response = google.sheets('v4').spreadsheets.values.append(request)

  return response.then((res) => {
    return {r: res}
  }).catch((err) => {
    return {e: err}
  })
});

