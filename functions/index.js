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

  functions.logger.log(vals)
  functions.logger.log(typeof vals)

  const request = {
    spreadsheetId: config.spreadsheet_id,
    auth: jwt,
    valueInputOption: 'RAW',
    range: 'queue!A1:A10000',
    resource: { values: vals }
  };

  const response = google.sheets('v4').spreadsheets.values.append(request)

  return response.then((res) => {
    return {r: res}
  }).catch((err) => {
    return {e: err}
  })
});



exports.saveToSheets = functions.https.onCall((data, context) => {
  functions.logger.log("App context: ", context.app);
  const jwt = new google.auth.JWT(
    config.client_email,
    null,
    config.private_key,
    ['https://www.googleapis.com/auth/spreadsheets']
  )

  let save_data = Object.entries(data.save);
  let vals = [[save_data[1][1][1]]]
  let user = save_data[0][1][1];

  functions.logger.log(vals)
  functions.logger.log(typeof vals)

  const request = {
    spreadsheetId: config.spreadsheet_id,
    auth: jwt,
    valueInputOption: 'RAW',
    range: `saves!C${user}:C${user}`,
    resource: { values: vals }
  };

  const response = google.sheets('v4').spreadsheets.values.update(request)


  return response.then((res) => {
    return {r: res}
  }).catch((err) => {
    return {e: err}
  })
});

exports.loadFromSheets = functions.https.onCall((data, context) => {
  const jwt = new google.auth.JWT(
    config.client_email,
    null,
    config.private_key,
    ['https://www.googleapis.com/auth/spreadsheets']
  )

  let user_data = Object.entries(data.user);
  functions.logger.log(user_data[0][1][1])
  const request = {
    spreadsheetId: config.spreadsheet_id,
    auth: jwt,
    range: `saves!A${user_data[0][1][1]}:C${user_data[0][1][1]}`,
  };

  const response = google.sheets('v4').spreadsheets.values.get(request)

  return response.then((res) => {
    return {r: res}
  }).catch((err) => {
    return {e: err}
  })
});