const functions = require('firebase-functions');
const admin = require('firebase-admin');
var serviceAccount = require("./permissions.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://recyclables-telegram-bot.firebaseio.com"
});

const express = require('express');
const app = express();
const db = admin.firestore();
const cors = require('cors');

const validateFirebaseIdToken = async (req, res, next) => {
  let auth = req.headers.authorization;

  if ((!auth || !auth.startsWith('Bearer ')) && !(req.cookies && req.cookies.__session)) {
    console.error('No Firebase ID Token was passed as a Bearer token in the Authorization header.',
        'Make sure you authorize your request by providing the following HTTP header:',
        'Authorization: Bearer <Firebase ID Token>',
        'or by passing a "__session" cookie.');
    res.status(401).send({ message: 'Unauthorized' });
    return;
  }

  let api_key;
  if (auth && auth.startsWith('Bearer ')) {
    // Read the API Key from the Authorization header.
    api_key = auth.split('Bearer ')[1];
  } else if (req.cookies) {
    // Read the API Key from cookie.
    api_key = req.cookies.__session;
  } else {
    // No token and no cookie
    res.status(401).send({ message: 'Unauthorized' });
  }

  try {
    // let decodedIdToken = await admin.auth().verifyIdToken(api_key);
    let decodedIdToken = 'AIzaSyDAIotF6Js8nGViHT1kepkmeEU1qKQhdEc';
    let encodedData = Buffer.from(decodedIdToken).toString('base64');
    req.user = encodedData;
    if (api_key === encodedData) {
      next();
      return;
    } else {
      res.status(401).send({ message: 'Unauthorized' });
    }
  } catch (error) {
    console.error('Error while verifying Firebase ID Token:', error);
    res.status(401).send({ message: 'Unauthorized' });
    // return;
  }
};

// Automatically allow cross-origin requests
app.use(cors({ origin: true } )); // to allow us to go into another domain of origin
app.use(validateFirebaseIdToken); // to allow only users with API key to access HTTP endpoint

//Routes
//Get dates
app.get('/api/getDates/:day1/:day2', (req, res) => {
  (async () => {
    // if (req.params.key == API_KEY) {
    // }
    try
    {
      // const document = db.collection('users').doc();
      let day1 = parseInt(req.params.day1);
      let day2 = parseInt(req.params.day2);
      let response= {};
      let returnDates= [];
      let today = new Date();
      let date = today.getDate();
      let day = today.getDay(); // 0 for Sunday, datefirst will be Next Monday
      let datefirst = new Date(today.setDate(date - day + 1)); // Monday, today changes to datefirst
      // Set default to thisFri and thisSat
      let dayDiff = day2 - day1;
      let date1 = new Date(datefirst.setDate(datefirst.getDate() + day1 - 1));
      let date2 = new Date(datefirst.setDate(datefirst.getDate() + dayDiff));
      if (day >= day1) { // Past Friday
        date1 = new Date(date1.setDate(date1.getDate() + 7)); // Next Friday, date1 changes to next fri
      }
      if (day >= day2) { // Past Saturday
        date2 = new Date(date2.setDate(date2.getDate() + 7)); // Next Saturday, date2 changes to next sat
      }

      // Count the number of orders
      let query = db.collection('shards');
      let friCount = 0;
      let satCount = 0;
      await query.get().then(querySnapshot => {
        let docs = querySnapshot.docs; //all the orders

        for (let doc of docs) { //each shard
          friCount += doc.data().count_fri;
          satCount += doc.data().count_sat;
        }
        return [friCount, satCount];
      })
      let friSlots = 10 - friCount;
      let satSlots = 10 - satCount;
      let firstSatMonth = new Date();
      firstSatMonth = new Date(firstSatMonth.setDate(date2.getDate() + 7));
      if (firstSatMonth.getDate().toString().length === 1 && firstSatMonth.getDate() <= 7) {
        satSlots = 0;
      }
      // Check if there are slots
      if (friSlots) {
        returnDates.push(date1);
      }
      if (satSlots) {
        returnDates.push(date2);
      }
      if (!friSlots && !satSlots) {
        response = "*Sorry, our collection slots are full, please try again next week!* \n\nType /cancel to exit the bot.";
      }

      let daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
      if (returnDates.length > 0) {
        returnDates.sort((a, b) => a - b);
        for (var d = 0; d < returnDates.length; d++) {
          returnDates[d] = daysOfWeek[returnDates[d].getDay()] + ' (' + returnDates[d].getDate().toString().padStart(2, "0") + '/' + (1 + returnDates[d].getMonth()).toString().padStart(2, "0") + '/' + returnDates[d].getFullYear() + ')';
        }
        response['dates'] = returnDates
      }
      return res.status(200).send(response);
    }
    catch (error)
    {
      console.log(error);
      return res.status(500).send(error);
    }
  })();
});

// Export the API to Firebase Cloud Functions
exports.app = functions.https.onRequest(app); // call function when there is a new request