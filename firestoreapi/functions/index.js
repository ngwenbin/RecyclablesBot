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
    // let split = auth.split('Bearer ')
    // if (split.length !== 2) {
    //   return res.status(401).send({ message: 'Unauthorized' });
    // } else {
    api_key = auth.split('Bearer ')[1];
    // }
  } else if (req.cookies) {
    // Read the API Key from cookie.
    api_key = req.cookies.__session;
  } else {
    // No token and no cookie
    return res.status(401).send({ message: 'Unauthorized' });
    // return;
  }

  try {
    // let decodedIdToken = await admin.auth().verifyIdToken(api_key);
    let decodedIdToken = 'AIzaSyDAIotF6Js8nGViHT1kepkmeEU1qKQhdEc';
    let encodedData = Buffer.from(decodedIdToken).toString('base64');    // console.log('ID Token correctly decoded', decodedIdToken);
    req.user = encodedData;
    if (api_key === encodedData) {
      next();
      return;
    } else {
      return res.status(401).send({ message: 'Unauthorized' });
    }
  } catch (error) {
    console.error('Error while verifying Firebase ID Token:', error);
    return res.status(401).send({ message: 'Unauthorized' });
    // return;
  }
};

// Automatically allow cross-origin requests
app.use(cors({ origin: true } )); // to allow us to go into another domain of origin
app.use(validateFirebaseIdToken); // to allow only users with API key to access HTTP endpoint

//Routes
// app.get('/hello-world', (req, res) => {
//     return res.status(200).send("Hello World!");
// })

//Write (POST)
// app.post('/api/create', (req, res) => {
//   (async () => {
//     try
//     {
//       await db.collection('orders').doc('/' + req.body.id + '/')
//       .create({
//         weight: req.body.weight,
//         c_id: req.body.c_id,
//         completed: req.body.completed,
//         u_id: req.body.u_id
//       })

//       return res.status(200).send();
//     }
//     catch(error) {
//       console.log(error);
//       return res.status(500).send(error);
//     }

//   })();
// });

//Read (GET)
//read individual docs based on ID
// app.get('/api/read/:id', (req, res) => {
//   (async () => {
//     try
//     {
//       const document = db.collection('users').doc(req.params.id);
//       let user = await document.get()
//       let response = user.data();
//       return res.status(200).send(response);
//     }
//     catch (error)
//     {
//       console.log(error);
//       return res.status(500).send(error);
//     }
//   })();
// });

// let shards = db.collection("shards");
// for (var shard in shards) {
//   total += shard.get().to_dict().get("count", 0)
// }

//read date
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
      // today = new Date(today.setDate(today.getDate() + 2));
      let date = today.getDate();
      // let day = 0;
      let day = today.getDay(); // 0 for Sunday, datefirst will be Next Monday
      // let time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
      let datefirst = new Date(today.setDate(date - day + 1)); // Monday, today changes to datefirst
      // if (day == 6) { // Saturday
      //   datefirst = new Date(today.setDate(datefirst.getDate() + 7)); // Next Monday, today changes to datefirst
      // }
      // Set default to thisFri and thisSat
      let dayDiff = day2 - day1;
      let date1 = new Date(datefirst.setDate(datefirst.getDate() + day1 - 1));
      let date2 = new Date(datefirst.setDate(datefirst.getDate() + dayDiff));
      // console.log(today); // datefirst
      // console.log(datefirst); // date2
      // console.log(date1);
      // console.log(date2);
      if (day >= day1) { // Past Friday
        date1 = new Date(date1.setDate(date1.getDate() + 7)); // Next Friday, date1 changes to next fri
      }
      if (day >= day2) { // Past Saturday
        date2 = new Date(date2.setDate(date2.getDate() + 7)); // Next Saturday, date2 changes to next sat
      }
      // returnDates.push(date1, date2);

      // Count the number of orders
      let query = db.collection('shards');
      let friCount = 0
      let satCount = 0
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
      // Check if there are slots
      if (friSlots) {
        returnDates.push(date1);
      }
      if (satSlots) {
        returnDates.push(date2);
      } else {
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
      // return res.json({'dates': returnDates});
      return res.status(200).send(response);
      // return returnDates; //array of dates for user to select: Friday (DD/MM/YY), Saturday (DD/MM/YY)
      // return response; //array of orders on the said date
        // const selectedItem = {
          //   id: doc.id,
          //   weight: doc.data().actual_weight,
          //   c_id: doc.data().collectorid,
          //   completed: doc.data().completed,
          //   timeslot: doc.data().timeslot,
          //   userid: doc.data().userid
          // };
          // if (selectedItem.timeslot == ) {
          //   response.push(selectedItem);
          // }

        // Checking S1, F2, S2 slots
        // if (day == 5 && time > '02:00:00' || day == 6 && time < '02:00:00') { // Fri after 2am to Sat before 2am
        //   // push nextFri, thisSat (if got slots), nextSat (if thisSat no slots)
        //   if (nextFriCount < 10) { // Next Fri's slots avail
        //       returnDates.push(nextFri);
        //     }
        //     if (thisSatCount < 10) { // This Sat's slots avail
        //       returnDates.push(thisSat);
        //     } else if (nextSatCount < 10) { // Next Sat's slots avail
        //       returnDates.push(nextSat);
        //     } else { // None of this and next week's slots are avail
        //       unavailSlots();
        //     }
        // // Checking F2, S2 slots
        // } else if (day == 6 && time > '02:00:00' || day == 0) { // Sat after 2am to Sun
        //     if (nextFriCount < 10) { // Next Fri's slots avail
        //       returnDates.push(nextFri);
        //     }
        //     if (nextSatCount < 10) { // Next Sat's slots avail
        //       returnDates.push(nextSat);
        //     } else { // None of next week's slots are avail
        //       unavailSlots();
        //     }
        // // Checking F1, S1, F2, S2 slots
        // } else { // Mon to Fri before 2am
        //   if (thisFriCount < 10) { // This Fri's slots avail
        //     returnDates.push(thisFri);
        //   } else if (nextFriCount < 10) { // Next Fri's slots avail
        //     returnDates.push(nextFri);
        //   }
        //   if (thisSatCount < 10) { // This Sat's slots avail
        //     returnDates.push(thisSat);
        //   } else if (nextSatCount < 10) { // Next Sat's slots avail
        //     returnDates.push(nextSat);
        //   } else { // None of this and next week's slots are avail
        //     unavailSlots();
        //   }
        // }

      // let user = await document.get()
      // let orders = user.data().u_orders;
      // for (order in orders) {

      // }
    }
    catch (error)
    {
      console.log(error);
      return res.status(500).send(error);
    }
  })();
});

//read all docs at once
// app.get('/api/read', (req, res) => {
//   (async () => {
//     try
//     {
//       let query = db.collection('users');
//       let response = [];

//       await query.get().then(querySnapshot => {
//         let docs = querySnapshot.docs; //the result of the query

//         for (let doc of docs)
//         {
//           const selectedItem = {
//             id: doc.id,
//             name: doc.data().username,
//             address: doc.data().address,
//             userid: doc.data().userid,
//           };
//           response.push(selectedItem);
//         }
//         return response; // for each to return a value
//       })
//       return res.status(200).send(response);
//     }
//     catch (error)
//     {
//       console.log(error);
//       return res.status(500).send(error);
//     }

//   })();
// })

// Export the API to Firebase Cloud Functions
exports.app = functions.https.onRequest(app); // call function when there is a new request
// // Create and Deploy Your First Cloud Functions
// // https://firebase.google.com/docs/functions/write-firebase-functions
//
// exports.helloWorld = functions.https.onRequest((request, response) => {
//  response.send("Hello from Firebase!");
// });
exports.corsEnabledFunctionAuth = (req, res) => {
  // Set CORS headers for preflight requests
  // Allows GETs from origin https://mydomain.com with Authorization header

  // res.set('Access-Control-Allow-Origin', 'https://mydomain.com');
  res.set('Access-Control-Allow-Credentials', 'true');

  // if (req.method === 'OPTIONS') {
  //   // Send response to OPTIONS requests
  //   res.set('Access-Control-Allow-Methods', 'GET');
  //   res.set('Access-Control-Allow-Headers', 'Authorization');
  //   res.set('Access-Control-Max-Age', '3600');
  //   res.status(204).send('');
  // } else {
  //   res.send('Hello World!');
  // }
};