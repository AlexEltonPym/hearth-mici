import React, { Component } from 'react';

import { Typography, Grid } from '@material-ui/core'


import './App.css';



function importAll(r) {
  return r.keys().map(r);
}

const images = importAll(require.context('./cards', false, /\.(png|jpe?g|svg)$/));
const blanks = importAll(require.context('./blankCards', false, /\.(png|jpe?g|svg)$/));

class App extends Component {

  constructor(props) {
    super(props)
    this.state = {
      keywords: ['Taunt', 'Lifelink', 'Charge'],
    };
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

        <div className="App-header">
          <p>
            Now it is time to build your own
        </p>
        </div>

        {/* <div style={{ padding: '0 10%' }}>
          <Grid style={{ paddingTop: '100px' }} container>
            {blanks.map((b) => {
              return (
                <Grid key={b} item xs={12} sm={12} md={6} xl={12}>
                  {b.includes('creature') && <img src={b} style={{ height: 400 }} />}
                </Grid>
              );
            })}
          </Grid>
        </div> */}

        <div>
        <iframe
            style={{
              border: "none",
              width: "100%",
              height: "100vh",
             
            }}

            srcDoc={`
            <head>
              <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/0.10.2/p5.min.js"></script>
            </head>
            <body style="margin: 0; padding: 0; height: 100%; overflow: hidden; width: 100%; position: fixed;">      
              <script> 
              let blank;
              let imgBG;
              let belwe;
              
              const imgScale = 0.8
              const keywords = [];
              const textpix = 32;
              const mousePadding = 10;
              
              let theMouse;
              
              let mana = 1;
              let power = 1;
              let toughness = 1;
              
              let ganImages = [];
              
              function preload() {
                blank = loadImage("https://hearthmicihosting.imfast.io/src/spell.png");
                imgBG = loadImage("https://hearthmicihosting.imfast.io/src/GAN_sample.jpg");
                belwe = loadFont("https://hearthmicihosting.imfast.io/src/BelweBoldBT.ttf");
              
                for (let i = 0; i < 1000; i++) {
                  ganImages.push(loadImage("https://hearthmicihosting.imfast.io/src/images/sample_" + i + ".jpg"));
                }
              }
              
              let chosenImage;
              
              function setup() {
                createCanvas(windowWidth, windowHeight);
                imageMode(CENTER)
                textAlign(CENTER, CENTER);
                rectMode(CENTER);
                textFont(belwe);
                textSize(textpix);
              
                fill(255);
                noStroke();
                theMouse = new FancyMouse();
                let offset = -60;
              
              
                ["Taunt", "Lifesteal", "Charge"].map((k) => {
                  keywords.push(
                    new Keyword(k, width * 0.75, height / 2 + offset));
                  offset += 60;
                });
              
              
                chosenImage = random(ganImages);
              
              }
              
              function draw() {
                background(204, 231, 232);
                noStroke();
              
                image(chosenImage, width * 0.3, height * 0.38, 220, 220);
                image(blank, width * 0.3, height / 2,
                  blank.width * imgScale,
                  blank.height * imgScale);
              
                textSize(textpix);
              
                for (let label of keywords) {
                  label.display();
                }
                textSize(72);
                fill(255);
                stroke(0);
                text(mana, 71, 62);
                text(toughness, 293, 400);
                text(power, 73, 400);
              
              }
              
              
              function mousePressed() {
                submit();
                console.log(mouseX + " " + mouseY);
              
                if (dist(mouseX, mouseY, 71, 62) < 40) {
                  mana += keyIsPressed ? -1 : 1;
                }
              
                if (dist(mouseX, mouseY, 293, 400) < 40) {
                  toughness += keyIsPressed ? -1 : 1;
                }
              
                if (dist(mouseX, mouseY, 73, 400) < 40) {
                  power += keyIsPressed ? -1 : 1;
                }
                mana = constrain(mana, 0, 10);
                power = constrain(power, 0, 10);
              
                toughness = constrain(toughness, 0, 10);
              
                if (theMouse.busy) {
                  theMouse.busy = false;
                  theMouse.setOffset(0, 0);
              
                  theMouse.selectedLabel.stuckOnMouse = false;
                  theMouse.selectedLabel.inCard = mouseX < width / 2;
                  theMouse.selectedLabel = null;
              
                } else {
                  for (let label of keywords) {
                    if (label.mouseInRegion()) {
              
                      theMouse.setOffset(label.x, label.y);
                      theMouse.busy = true;
                      theMouse.selectedLabel = label;
                      label.stuckOnMouse = true;
                      break;
                    }
              
                  }
              
                }
              
              }
              
              
              class Keyword {
              
                constructor(title, x, y) {
                  this.title = title;
                  this.name = title.toLowerCase();
                  this.initialX = x;
                  this.initialY = y;
                  this.x = x;
                  this.y = y;
                  this.w = textWidth(title) + 10;
                  this.h = textpix + 10;
                  this.stuckOnMouse = false;
                  this.inCard = false;
              
                }
                mouseInRegion() {
                  return ((mouseX > this.x - this.w / 2 - mousePadding &&
                      mouseX < this.x + this.w / 2 + mousePadding) &&
                    (mouseY > this.y - this.h / 2 - mousePadding &&
                      mouseY < this.y + this.h / 2 + mousePadding));
                }
              
                display() {
                  if (this.stuckOnMouse) {
                    this.x = mouseX - theMouse.xOffset;
                    this.y = mouseY - theMouse.yOffset;
                  } else {
                    if (this.inCard) {
                      this.x = width * 0.3;
                      this.y = this.initialY * 0.6 + 215;
                    } else {
                      this.x = this.initialX;
                      this.y = this.initialY;
                    }
                  }
              
                  push();
                  translate(this.x, this.y);
                  let fillAlpha = this.stuckOnMouse ? 255 : (this.mouseInRegion() ? 200 : 150);
              
                  fill(255, this.inCard ? 0 : fillAlpha);
              
                  rect(0, 0, this.w, this.h, 4, 4);
                  fill(0, this.inCard ? 255 : fillAlpha);
                  text(this.title, 0, -8);
              
                  pop();
                }
              }
              
              class FancyMouse {
                constuctor() {
                  this.busy = false;
                  this.xOffset = 0;
                  this.yOffset = 0;
                  this.selectedLabel = null;
                }
                setOffset(xOff, yOff) {
                  this.xOffset = mouseX - xOff;
                  this.yOffset = mouseY - yOff;
                }
              
              
              }
              
              function submit() {
                let j = {};
                for (let k of keywords) {
                  if (k.inCard) {
                    j[k.name] = true;
                  }
                }
              
                j.power = power
                j.toughness = toughness
                j.mana = mana
                console.log(j);
              }
              
              function windowResized() {
                resizeCanvas(windowWidth, windowHeight);
              }

              </script>
            </body>
                  `}
            width={"100%"}
            sandbox="allow-scripts"
          />
        </div>
      </div>
    );
  }
  
}

export default App;
