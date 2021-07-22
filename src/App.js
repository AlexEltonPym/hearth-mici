import React, { Component } from 'react';

import { Typography, Grid } from '@material-ui/core'

import Draggable, {DraggableCore} from 'react-draggable'; 


import './App.css';
import Card from './Card.js';
import sketch from './sketch.js';
import * as p5 from "p5";
import P5Wrapper from "react-p5-wrapper";


function importAll(r) {
  return r.keys().map(r);
}

const images = importAll(require.context('./cards', false, /\.(png|jpe?g|svg)$/));
const blanks = importAll(require.context('./blankCards', false, /\.(png|jpe?g|svg)$/));


const card_types = ["creature", "spell", "weapon"];


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



    let cardA = new Card("cardA", 1, 1, 1, true, true, false, 0)
    let cardB = new Card("cardB", 1, 1, 1, true, true, false, 1)
    let cardC = new Card("cardC", 1, 1, 1, true, true, false, 2)

    this.state = {
      keywords: ['Taunt', 'Lifelink', 'Charge'],
      card_sources: {
        'creature': creatureSrc,
        'spell': spellSrc,
        'weapon': weaponSrc,
      },
      cards: {
        'cardA': cardA,
        'cardB': cardB,
        'cardC': cardC
      }
    };


    this.handleClick = this.handleClick.bind(this);
  }

  handleClick(e) {
    console.log(this.state.cards[e.target.id]);
    this.state.cards[e.target.id].card_type = (this.state.cards[e.target.id].card_type+1)%3;
    this.setState(this.state) //dont do this
  }
  render() {


    return (
      <div className="App">
         <header className="App-header">
          <p>
            Please check out the available cards:
        </p>
        </header>

        <div style={{ padding: '0 10%' }}>
          {['neutral', 'mage', 'warrior'].map((toDisplay) => {
            return (
              <div key={toDisplay}>
                <Typography variant="h2" style={{ paddingTop: '100px' }} >{toDisplay}</Typography>
                <Grid key={toDisplay} container>
                  {

                    images.reduce(function (result, i) {
                      if (i.includes(toDisplay)) {
                        result.push((
                          <Grid key={i} item xs>
                            <img src={i} height={300} />
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

        <div>
          <p>
            Now it is time to build your own
        </p>
        </div> 

        <div>


        </div>
        <P5Wrapper sketch={sketch} />;



      </div>


    );
  }

}

export default App;
