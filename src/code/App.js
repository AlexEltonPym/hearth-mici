import React, { Component } from 'react';

import { Typography, Grid } from '@material-ui/core'


import '../style/App.css';
import bg_img from '../images/bigger_paper.jpg';
import spell_img from '../images/blank_cards/spell.png'
import creature_img from '../images/blank_cards/creature.png'
import weapon_img from '../images/blank_cards/weapon.png'
import full_blank_creature_img from '../images/blank_cards/fullBlankCreature.png'
import gan_img from '../images/GAN_sample.jpg'
import hs_font from '../fonts/BelweBoldBT.ttf'

import sketch from './sketch.js';
import P5Wrapper from "react-p5-wrapper";


import firebase from "firebase/app";
import "firebase/functions";

firebase.initializeApp({
  projectId: 'hearth-mici',
  apiKey: 'AIzaSyAdJ-9ONMVy2RcpD-i3qpzcB_Rui0pJzLA',
});



function importAll(r) {
  return r.keys().map(r);
}


const images = importAll(require.context('../images/cards', false, /\.(png|jpe?g|svg)$/));
const blanks = importAll(require.context('../images/blank_cards', false, /\.(png|jpe?g|svg)$/));

const gan_imgs = importAll(require.context('../images/gan_samples', false, /\.(png|jpe?g|svg)$/));


class App extends Component {

  constructor(props) {
    super(props)

    let creatureSrc = blanks.filter((value) => {
      return value.includes("creature");
    })[0];
    let spellSrc = blanks.filter((value) => {
      return value.includes("spell");
    })[0];
    let weaponSrc = blanks.filter((value) => {
      return value.includes("weapon");
    })[0];

    this.state = {

      card_sources: {
        'creature': creatureSrc,
        'spell': spellSrc,
        'weapon': weaponSrc,
      },

      sheetLoaded: false,

    };

    this.send_to_google_sheets.bind(this);
    this.save_to_google_sheets.bind(this);
    this.load_from_google_sheets.bind(this);
  }


  send_to_google_sheets(submissions){
    return firebase.functions().httpsCallable('sendToSheets')({submissions: Object.entries(submissions)})
  }

  save_to_google_sheets(save){
    return firebase.functions().httpsCallable('saveToSheets')({save: Object.entries(save)})
  }

  load_from_google_sheets(user){
    let user_data = {user: user}
    return firebase.functions().httpsCallable('loadFromSheets')({user: Object.entries(user_data)})
  }

  render() {


    return (
      <div className="App">


         <span className="banner"><b>Step 1: </b>Please check out the available cards:</span>

        <div style={{ padding: '0 10%' }}>
          {['hunter', 'mage', 'warrior', 'neutral'].map((toDisplay) => {
            return (
              <div key={toDisplay}>
                <Typography variant="h2" style={{ paddingTop: '100px' }} >{toDisplay[0].toUpperCase() + toDisplay.substring(1)}</Typography>
                <Grid key={toDisplay} container>
                  {

                    images.reduce(function (result, i) {
                      if (i.includes(toDisplay)) {
                        result.push((
                          <Grid key={i} item xs={3}>
                            <img src={i} height={300} alt={""} />
                          </Grid>
                        ));
                      }
                      return result;
                    }, [])

                  }

                </Grid>
              </div>
            )
          })}
        </div>

        <span style={{marginBottom: "25vh"}} className="banner"><b>Step 2: </b>Now it's time to build your own cards...</span>


        <P5Wrapper sketch={sketch}
         bg_img={bg_img}
         spell_img={spell_img} 
         creature_img={creature_img}
          weapon_img={weapon_img} 
          full_blank_creature_img={full_blank_creature_img}
          gan_img={gan_img}
          gan_imgs={gan_imgs}
          hs_font={hs_font}
          send_to_google_sheets={this.send_to_google_sheets}
          save_to_google_sheets={this.save_to_google_sheets}
          load_from_google_sheets={this.load_from_google_sheets}
          />



      </div>


    );
  }

}

export default App;
