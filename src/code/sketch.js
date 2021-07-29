



 /* eslint eqeqeq: "off", no-unused-vars: "off" */

export default function sketch(p){

let blank_spell_img, blank_creature_img, blank_weapon_img, full_blank_creature_img;
let bg;
let GAN_imgs = [];
let flavour_img, masked_flavour_ellipse, masked_flavour_rect;


const buttons = [];
let button_id = 0;

const effects = [];

let experiments = ["mvw", "2mur", "longer_game"];
let user = ""

const cards = [];
const card_num = 3;
const card_types = ["spell", "minion", "weapon"]

const method_names = ["randomly", "targeted", "all", "aura"];
const target_names = ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems", "weapons"];
const target_names_singular = ["minion", "hero", "minion or hero", "murloc", "beast", "demon", "totem", "weapon"]
const filter_names = ["enemy", "friendly", "all"];
const duration_names = ["turn", "permanently"];
const param_format_names = ["x", "x/x", "k", "c"];
const effect_names = ["Deal damage", "Destroy", "Heal", "Gain armour", "Change stats", "Set stats", "Give keyword", "Return to hand", "Draw", "Gain mana", "Summon: ", "Battlecry: ", "Deathrattle: "]
const keywords = ["Taunt", "Charge", "Lifesteal", "Spell damage +1", "Divine shield", "Poisonous", "Windfury", "Frozen"]
const all_creature_types = ["murloc", "beast", "demon", "totem", "dragon", "pirate", "mech", "elemental"]
const creature_types = ["Murloc", "Beast", "Demon", "Totem"]

const survey_topics = ["none", "methods", "filters", "targets", "duration", "params"];
let current_survey_topic = 0;

let survey_drop_target = null;


const font_pixels = 24;
const smaller_font_size = 20;
let hearthstone_font;
const mouse_padding = 1;
let w_padding, h_padding;
let grid_w_padding, grid_h_padding;

let theMouse;
let setupDone = false;
let hoveredOption = -1;

let editing = "none";
let editing_card = null;
let effect_to_remove = null;
let editX = 0;
let editY = 0;

let simCount = 3;
let simulating = false;
let simDuration = 2000;
let simTime = -simDuration;

let mouse_over_queuer;

let simResults = null;
let simTurns = null;

let props;


p.myCustomRedrawAccordingToNewPropsHandler = (_props) => {
  props = _props;
}

p.preload = () => {
  bg = p.loadImage(props.bg_img)
  blank_spell_img = p.loadImage(props.spell_img);
  blank_weapon_img = p.loadImage(props.weapon_img)
  blank_creature_img = p.loadImage(props.creature_img)
  full_blank_creature_img = p.loadImage(props.full_blank_creature_img);
  flavour_img = p.loadImage(props.gan_img)
  hearthstone_font = p.loadFont(props.hs_font);
}


p.setup = () => {
  p.createCanvas(p.windowWidth, p.windowHeight);
  user = p.getURLParams().user;

  theMouse = new p.FancyMouse();


  h_padding = p.height * 0.1;
  w_padding = p.width * 0.2;
  grid_h_padding = p.height * 0.2;
  grid_w_padding = p.width * 0.1;
  p.imageMode(p.CENTER)
  p.rectMode(p.CENTER);
  p.textFont(hearthstone_font);
  p.textSize(font_pixels);
  p.fill(255);
  p.noStroke();






  p.register_all();


  for (let i = 0; i < card_num; i++) {
    cards.push(new p.Card(i, "mvw"));
  }

  p.resize_all();


  let ellipse_mask = p.createGraphics(p.width, p.height);
  ellipse_mask.ellipse(p.width / 2, p.height / 2+50, 900, 840)

  let rect_mask = p.createGraphics(p.width, p.height);
  rect_mask.rect(p.width / 2-450, p.height / 2 - 300, 900, 800)

  masked_flavour_ellipse = flavour_img.get();
  masked_flavour_ellipse.mask(ellipse_mask)
  masked_flavour_rect = flavour_img.get();
  masked_flavour_rect.mask(rect_mask)


  setupDone = true;

}


p.draw = () => {
  p.background(255)
  p.textAlign(p.LEFT, p.CENTER);
  p.image(bg, p.width / 2, p.height / 2, p.width, p.height);

  for (let c of cards) {
    c.run();
  }

  for (let b of buttons) {
    b.run();
  }

  if(theMouse.busy && current_survey_topic == 0){
    p.push();
    p.translate(p.mouseX-theMouse.xOffset, p.mouseY-theMouse.yOffset)
    p.textSize(28)
    p.text(theMouse.effect.label_name, 0, 0)
    p.pop();
  }

  p.draw_edit_overlay();

  p.sim_overlay();


  if(survey_topics[current_survey_topic] != "none"){
    p.draw_survey(); 
  }
    
}



p.draw_survey = () => {
  p.push();
  p.textAlign(p.CENTER, p.CENTER)
  p.textSize(font_pixels)

  p.rectMode(p.CENTER)
  p.background(0, 100)

  let setting = theMouse.effect.settings[survey_topics[current_survey_topic]]
  let options = setting[0]

    
  if(setting[0][0] == "x"){
    options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
  } else if(setting[0][0] == "k"){
    options = keywords
  } else if(setting[0][0] == "c"){
    options = creature_types;
  }
  

  if(options[0] == "x/x"){
    for(let attack = 1; attack < 11; attack++){
      for(let defense = 1; defense < 11; defense++){
        let xPos = p.map(attack, 1, 10, grid_w_padding, p.width-grid_w_padding);
        let yPos = p.map(defense, 1, 10, grid_h_padding, p.height-grid_h_padding);
        let boxWidth = (p.width-grid_w_padding*2)/10;
        let boxHeight = (p.height-grid_h_padding*2)/10;

        if(p.mouseX > xPos - boxWidth/2 && p.mouseX < xPos + boxWidth/2 &&
          p.mouseY > yPos - boxHeight/2 && p.mouseY < yPos+boxHeight/2){
              p.fill(255, 100);
          } else {
            p.fill(255, 0);
          }
          p.rect(xPos, yPos, boxWidth, boxHeight);
          p.fill(255);
          p.text(attack + "/" + defense, xPos, yPos-10)
      }
    }
  } else {


  p.textSize(40);
  p.fill(255)
  p.text(theMouse.effect.label_name + "...", p.width/2, p.height*0.1);

  p.textSize(font_pixels)
  p.rectMode(p.CENTER)

  let optionButtonWidth = (p.width/options.length)*0.5;
  let optionButtonHeight = p.height*0.10;
  let optionButtonsPadding = p.width*0.25;

  for(let [index, option] of options.entries()){
    let xPos = p.map(index, 0, options.length-1, optionButtonsPadding, p.width-optionButtonsPadding);
    if(p.mouseX > xPos-optionButtonWidth/2 && p.mouseX < xPos + optionButtonWidth/2){
      p.fill(255, 100)
      hoveredOption = index;
    } else {
      p.fill(255, 50)
    }
    p.rect(xPos, p.height*0.5, optionButtonWidth, optionButtonHeight, 16);
    p.fill(255);

    let optionString = option.toString();
    optionString = optionString[0].toUpperCase() + optionString.substring(1)
    optionString = optionString.split(" ").join("\n");

    p.text(optionString, xPos, p.height/2)
  }
}
  
p.pop();
}


p.mousePressedWhileSurveying = () => {
  if(p.progressSurveyThroughIssues()){
    return
  }


  let setting = theMouse.effect.settings[survey_topics[current_survey_topic]];
  let options = setting[0]
  if(options[0] == "x"){
    options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  } else if (options[0] == "k"){
    options = keywords;
  } else if (options[0] == "c"){
    options = creature_types;
  }
  
  if(options[0] == "x/x"){
    setting[1] = {x: p.floor(p.map(p.mouseX, 0, p.width, 1, 11)),
                  y: p.floor(p.map(p.mouseY, 0, p.height, 1, 11))}
  } else {
    setting[1] = options[hoveredOption];
  }
  
  current_survey_topic++;

  if(p.progressSurveyThroughIssues()){
    return
  }

}


p.mousePressedWhileNotSurveying = () => {
  let clickedCard = null;

  for (let c of cards) {
    if (c.mouseInImg()) {
      clickedCard = c;
    }
  }


  if(clickedCard){
    if(theMouse.busy){ //dropping effect onto a card
      p.dropEffectOnCard(clickedCard)
    } else { //clicking on a card generally
      p.clickToEditCard(clickedCard)
    }
  } else {
    if(theMouse.busy){ //clicked away to drop label
      theMouse.busy = false;
      theMouse.setOffset(0, 0);
      theMouse.effect = null;
    } else { //other clicks

      if(mouse_over_queuer){
        p.add_to_queue();
      }

      p.mouse_click_while_editing();
      

      for (let b of buttons) { //clicking on a button with an empty hand
        if (b.mouseInRegion()) {
          theMouse.busy = true;
          theMouse.setOffset(b.text_x, b.text_y);
          theMouse.effect = JSON.parse(JSON.stringify(effects[b.button_name]));

          break;
        }
      }
    }
  }

}



//returns true if you need to return out of mouse
p.progressSurveyThroughIssues = () => {
  if(current_survey_topic == survey_topics.length){
    p.finished_survey();
    return true;
  }

  for(let i = 0; i < survey_topics.length; i++){
    if(theMouse.effect.settings[survey_topics[current_survey_topic]][0] == null ||
      (!param_format_names.includes(theMouse.effect.settings[survey_topics[current_survey_topic]][0][0]) &&
       theMouse.effect.settings[survey_topics[current_survey_topic]][0].length == 1)){
      current_survey_topic++;
      if(current_survey_topic == survey_topics.length){
        p.finished_survey();
        return true;
      }
    }
  }


  if(current_survey_topic == survey_topics.length){
    p.finished_survey();
    return true;
  }


  return false;
}

p.dropEffectOnCard = (c) => {
    current_survey_topic = 1;
    survey_drop_target = c;

    if(p.progressSurveyThroughIssues()){

      return
    }
}


p.clickToEditCard = (c) => {

  if(c.mouse_over_mana){
    editing = "mana";
    editing_card = c;
  } else if(c.mouse_over_power){
    editing = "power";
    editing_card = c;
  } else if(c.mouse_over_toughness && !(editing =="effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10)){
    editing = "toughness";
    editing_card = c;
  } else if(c.mouse_over_card_effect && !(editing =="effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10 )){
    editing = "effect";
    editX = c.hovered_effect.x + blank_spell_img.width/2;
    editY = c.hovered_effect.y + c.hovered_effect.effect_string_height/2;
    editing_card = c;
    effect_to_remove = c.hovered_effect;
   } else if(editing=="effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10){
      editing_card.effects.splice(editing_card.effects.indexOf(effect_to_remove), 1);
      editing = "none";
    } else {
    editing = "none";
  }
}


p.mouse_click_while_editing = () => {
  if(editing == "mana"){
    if(p.dist(p.mouseX, p.mouseY, editX-60, editY-50)<40){
      editing_card.mana--;
    } else if(p.dist(p.mouseX, p.mouseY, editX+60, editY-50)<40){
      editing_card.mana++;
    } else {
      editing = "none"
    }
    editing_card.mana = p.constrain(editing_card.mana, 0, 10)
  } else if(editing == "power"){

    if(p.dist(p.mouseX, p.mouseY, editX-60, editY+50)<40){
      editing_card.power--;
    } else if(p.dist(p.mouseX, p.mouseY, editX+60, editY+50)<40){
      editing_card.power++;
    } else {
      editing = "none"
    }
    editing_card.power = p.constrain(editing_card.power, 0, 10)
  } else if(editing == "toughness"){

    if(p.dist(p.mouseX, p.mouseY, editX-60, editY+50)<40){
      editing_card.toughness--;
    } else if(p.dist(p.mouseX, p.mouseY, editX+60, editY+50)<40){
      editing_card.toughness++;
    } else {
      editing = "none"
    }
    editing_card.toughness = p.constrain(editing_card.toughness, 1, 10)
  } else if(editing == "effect"){
    editing = "none";
  }
} 


p.draw_edit_overlay = () => {
  p.push();
  if(editing != "none"){
    p.translate(editX, editY)
    p.noStroke();
    if(editing=="effect"){
      p.rotate(p.QUARTER_PI);
      p.fill(0);
      p.rect(0, 0, 22, 6);
      p.rect(0, 0, 6, 22);
      p.fill(255);
      p.rect(0, 0, 20, 4);
      p.rect(0, 0, 4, 20);
 
    } else {
      p.fill(0);
      p.rect(-60, editing=="mana"?-50:75, 32, 8);
      p.rect(60, editing=="mana"?-50:75, 32, 8);
      p.rect(60, editing=="mana"?-50:75, 8, 32);
      p.fill(255);
      p.rect(-60, editing=="mana"?-50:75, 30, 6);
      p.rect(60, editing=="mana"?-50:75, 30, 6);
      p.rect(60, editing=="mana"?-50:75, 6, 30);
    }
  }
  p.pop();
}

p.mousePressed = () => {
  if(setupDone){
    if(survey_topics[current_survey_topic] != "none"){
      p.mousePressedWhileSurveying();
    } else {
      p.mousePressedWhileNotSurveying();
    }
}
}

p.finished_survey = () => {

  survey_drop_target.effects.push(JSON.parse(JSON.stringify(theMouse.effect)))
  current_survey_topic = 0;
  theMouse.effect = null;
  theMouse.busy = false;
}

p.keyPressed = () => {
  if (p.key == ' ' && !simulating) {
    simResults = null;
    simTurns = null;
    simulating = true;
    simTime = simCount;
    p.submit();
  }

}

p.windowResized = () => {
  p.resizeCanvas(p.windowWidth, p.windowHeight);
  p.resize_all();
}

p.add_to_queue = () => {
  if(!simulating){
    simulating = true;
    simTime = p.millis();
    p.submit();
  }
}

p.sim_overlay = () => {
  p.push();
  let queur_x = p.map(2, 0, 3, w_padding, p.width-w_padding);
  let queur_y = p.height*0.85
  mouse_over_queuer = (p.mouseX > queur_x - 100 && p.mouseX < queur_x + 100 && p.mouseY > queur_y-30 && p.mouseY < queur_y+30)

  p.translate(queur_x, queur_y);

  if(mouse_over_queuer && !simulating){
    p.fill(255, 255);
  } else {
    p.fill(p.map(p.millis(), simTime, simTime+simDuration, 100, 255, true), 100)
  } 
  p.rect(0, 0, 200, 60, 4)


  p.fill(0, 255);
  p.textAlign(p.CENTER, p.CENTER)
  p.text(simulating?"Adding...":"Add to queue", 0, -4)

  p.rectMode(p.CORNER)

  // if(simulating)
  // p.fill(0)
  // p.rect(-100, -30, map(millis(), simTime, simTime+simDuration, 0, 200, true), 60, 4)


  p.pop();

  if(simulating){
    if(p.millis() > simTime+simDuration){
      simulating = false;
    }
  }
  // if (simulating) {
  //   simTime = constrain(simTime - random(0.001, 0.002), 0, simCount);

  //   let lw = map(simTime, 0, simCount, 0, 200);
  //   noStroke();
  //   p.fill(200);
  //   p.rect(width * 0.5 - 100, height * 0.85 - 16, 200, 40)
  //   p.fill(0)
  //   p.rect(width * 0.5 - 100, height * 0.85 - 16, lw, 40)
  //   p.fill(255);
  //   text("Simulating...", width * 0.5, height * 0.85)
  // } else {
  //   text("Press Spacebar to simulate", width / 2, height * 0.9);
  // }

  // if (simResults != null) {

  //   text("The win rate with your card is: " + simResults +
  //     "%\n" + "The average game lasted " + simTurns +
  //     " turns.", width * 0.5, height * 0.10);
  // }
}

p.submit = () => {
  let submissions = [];
  for(let c of cards){

    let card_submission = {
      id: c.card_id,
      exp: c.card_experiment,
      user: user,
      p: c.power,
      t: c.toughness,
      m: c.mana,
    }

    
    let repeat_checker = {};

    for (let e of c.effects) {
      if(repeat_checker[e.effect_short] == undefined){
        repeat_checker[e.effect_short] = 0;
      } else {
        repeat_checker[e.effect_short]++;
      }

      if(e.settings.methods[0] != null) card_submission[e.effect_short+"-method-"+repeat_checker[e.effect_short]] = e.settings.methods[1];
      if(e.settings.params[0] != null) card_submission[e.effect_short+"-param-"+repeat_checker[e.effect_short]] = e.settings.params[1];
      if(e.settings.targets[0] != null) card_submission[e.effect_short+"-target-"+repeat_checker[e.effect_short]] = e.settings.targets[1];
      if(e.settings.filters[0] != null) card_submission[e.effect_short+"-filter-"+repeat_checker[e.effect_short]] = e.settings.filters[1];
      if(e.settings.duration[0] != null) card_submission[e.effect_short+"-duration-"+repeat_checker[e.effect_short]] = e.settings.duration[1];

    }
    submissions[c.card_experiment+"-"+c.card_id] = card_submission;
 }


 p.send_to_google_sheets(submissions);

}


p.send_to_google_sheets = (submissions) => {

  for(let submission of submissions){
    console.log(submission)
    
  }

  // gapi.load('client', ()=>{
  //   gapi.client.init({ 'apiKey':  config.sheets_api_key}).then(()=>{
  //     gapi.client.sheets.spreadsheets.values.get({
  //       spreadsheetId: config.sheet_id,
  //       range: "queue!A1:D5"
  //     }).then((response) => {
  //       var result = response.result;
  //       var numRows = result.values ? result.values.length : 0;
  //       console.log(`${numRows} rows retrieved.`);
  //     });
  //   }); 
  // });







  // httpPost('https://hearth-mici-backend.loca.lt/get_winrates', submission, (response) => {
  //   simulating = false;
  //   simResults = round(JSON.parse(response).win_rate, 2);
  //   simTurns = round(JSON.parse(response).num_turns, 2);
  //   console.log(simResults, simTurns)
  // });


  // httpPost('https://sheets.googleapis.com/v4/spreadsheets/1TlgFYV4zwkyfwGq1DNU39Sq1kOsOaL3jfppokpmgX0w/values/queue!A1:E1:append?key='+config.sheets_api_key, {
  //   range: "queue!A1:E1",
  //   key: config.sheets_api_key,
  //   majorDimension: "ROWS",
  //   values: [
  //     ["Door", "$15", "2", "3/15/2016"],
  //     ["Engine", "$100", "1", "3/20/2016"],
  //   ],
  // }, (response) => {
  //   console.log(response)
  // });

}

p.resize_all = () => {
  for (let b of buttons) {
    b.resized();
  }

  for (let c of cards) {
    c.resized();
  }

}

p.register_effect = (effect_text, effect_short, method, param, targets, filters, duration) => {

  effects[effect_text] = new p.Effect(effect_text, effect_short, method, param, targets, filters, duration);
  buttons.push(new p.Button(effect_text, button_id++));
}

p.register_all = () => {

  p.register_effect("Deal damage", "dam",
    ["randomly", "targeted", "all"],
    ["x"],
    ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems"],
    ["enemy", "friendly", "all"],
    null);

  p.register_effect("Destroy", "des",
    ["randomly", "targeted", "all"],
    null,
    ["minions", "murlocs", "beasts", "demons", "totems", "weapons"],
    ["enemy", "friendly", "all"],
    null);

  p.register_effect("Heal", "hea",
    ["randomly", "targeted", "all"],
    ["x"],
    ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems"],
    ["enemy", "friendly", "all"],
    null);

  p.register_effect("Gain armour", "arm",
    null,
    ["x"],
    null,
    null,
    null);

  p.register_effect("Change stats", "cha",
    ["randomly", "targeted", "all", "aura"],
    ["x/x"],
    ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems", "weapons"],
    ["enemy", "friendly", "all"],
    ["turn", "permanently"]);

  p.register_effect("Set stats", "set",
    ["randomly", "targeted", "all", "aura"],
    ["x/x"],
    ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems", "weapons"],
    ["enemy", "friendly", "all"],
    ["turn", "permanently"]);


  p.register_effect("Give keyword", "giv",
    ["randomly", "targeted", "all", "aura"],
    ["k"],
    ["minions", "heroes", "minions or heroes", "murlocs", "beasts", "demons", "totems", "weapons"],
    ["enemy", "friendly", "all"],
    ["turn", "permanently"]);

  p.register_effect("Return to hand", "ret",
    ["randomly", "targeted", "all"],
    null,
    ["minions", "murlocs", "beasts", "demons", "totems"],
    ["enemy", "friendly", "all"],
    null);


  p.register_effect("Draw", "dra",
    null,
    ["x"],
    null,
    ["enemy", "friendly", "all"],
    null);


  p.register_effect("Gain mana", "gai",
    null,
    ["x"],
    null,
    ["enemy", "friendly", "all"],
    null);

  p.register_effect("Summon", "sum",
    null,
    ["x/x"],
    null,
    null,
    null);

    p.register_effect("Keyword", "key",
    null,
    ["k"],
    null,
    null,
    null);

    p.register_effect("Creature type", "cre",
    null,
    ["c"],
    null,
    null,
    null);



}


p.FancyMouse = class {
  constuctor(){
    this.busy = false;
    this.xOffset = 0;
    this.yOffset = 0;
    this.effect = null;
  }
  setOffset(buttonX, buttonY) {
    this.xOffset = p.mouseX - buttonX;
    this.yOffset = p.mouseY - buttonY;
  }
}





p.Effect = class {
  constructor(label_name,effect_short,methods, param_format, targets, filters, duration){
    this.x = 0;
    this.y = 0;

    this.effect_string = "";
    this.effect_string_height = 0;
    this.effect_string_width = blank_spell_img.width * 0.5;
    this.label_name = label_name;
    this.effect_short = effect_short;

    this.settings = {
      methods: [methods, ""],
      params: [param_format, ""],
      targets: [targets, ""],
      filters: [filters, ""],
      duration: [duration, ""]
    };
  }
}


p.Card = class {
  constructor(card_id, card_experiment) {
      this.y = 0;
      this.x = 0;
      this.w = blank_spell_img.width * 0.75;
      this.h = blank_spell_img.height * 0.75;
      this.oversized = false;


      this.class = "mage";
      this.type_id = 1;
      this.card_id = card_id;
      this.card_experiment = card_experiment;

      this.creature_type = "";
      this.mana = 5;
      this.power = 5;
      this.toughness = 5;
      this.keywords = [];
      this.effects = [];

      this.hovered_effect = null;
      this.mouse_over_card_effect = false;
      this.mouse_over_mana = false;
      this.mouse_over_power = false;
      this.mouse_over_toughness = false;


  }

  resized(){
      this.x = p.map(this.card_id + 1, 0, cards.length, w_padding, p.width - w_padding)
      this.y = p.height / 2;
  }

  run(){
      this.generate_effect_text();
      this.check_mouse_hovers();
      this.display();
  }

  generate_effect_text(){
      for (let e of this.effects) {
          e.effect_string = "";
          if(e.label_name == "Keyword" || e.label_name == "Creature type"){
              e.effect_string = e.settings.params[1];
          } else if(e.label_name == "Deal damage"){
              if(e.settings.methods[1] == "randomly"){
                  e.effect_string = "Randomly deal " + e.settings.params[1] + " damage to a ";
              } else if(e.settings.methods[1] == "targeted"){
                  e.effect_string = "Deal " + e.settings.params[1] + " damage to target ";
              } else {
                  e.effect_string = "Deal " + e.settings.params[1] + " damage to all "
              }

              e.effect_string += e.settings.filters[1]=="all"?"":e.settings.filters[1] + " " //remove "all all"
              if(e.settings.methods[1] == "all"){
                  e.effect_string += e.settings.targets[1]
              } else {
                  e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
              }
          } else if(e.label_name =="Destroy"){
              if(e.settings.methods[1] == "randomly"){
                  e.effect_string = "Randomly destroy a ";
              } else if(e.settings.methods[1] == "targeted"){
                  e.effect_string = "Destroy a target ";
              } else {
                  e.effect_string = "Destroy all "
              }
              e.effect_string += e.settings.filters[1]=="all"?"":e.settings.filters[1] + " " //remove "all all"
              if(e.settings.methods[1] == "all"){
                  e.effect_string += e.settings.targets[1]
              } else {
                  e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
              }
          } else if(e.label_name =="Heal"){
              if(e.settings.methods[1] == "randomly"){
                  e.effect_string = "Restore " + e.settings.params[1] + " health to a random ";
              } else if(e.settings.methods[1] == "targeted"){
                  e.effect_string = "Restore " + e.settings.params[1] + " health to a target ";
              } else {
                  e.effect_string = "Restore " + e.settings.params[1] + " health to all ";
              }
              e.effect_string += e.settings.filters[1]=="all"?"":e.settings.filters[1] + " " //remove "all all"
              if(e.settings.methods[1] == "all"){
                  e.effect_string += e.settings.targets[1]
              } else {
                  e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
              }                
          } else {
              e.effect_string = e.label_name
          }

          

          let estimatedCharactersPerLine = 20;
          let estimatedLines =  e.effect_string.length/estimatedCharactersPerLine;
          e.effect_string_height = smaller_font_size * estimatedLines + 30;
          
      }

  }

  display(){
    p.push();
    p.fill(0);
    p.textAlign(p.CENTER, p.CENTER)
      if(this.effects.length > 2){
          this.oversized = true;
      } else {
          this.oversized = false;
      }
      let flav;
      let forg;

      if (card_types[this.type_id] == "spell") {
          flav = masked_flavour_rect;
          forg = blank_spell_img;
      } else if (card_types[this.type_id] == "minion") {
          flav = masked_flavour_ellipse;
          forg = this.oversized ? full_blank_creature_img:blank_creature_img;
      } else {
          flav = masked_flavour_rect;
          forg = blank_weapon_img;
      }

      if(!this.oversized){
        p.image(flav, this.x + 5, this.y - 50, 300, 300)
      }
      p.image(forg, this.x, this.y, this.w, this.h);

      p.push();
      p.textSize(60);
      p.fill(255);
      p.strokeWeight(3);
      p.stroke(0);

      if (card_types[this.type_id] == "minion") {
        p.text(this.power, this.x-this.w/2.99, this.y+this.h/2.8)
        p.text(this.toughness, this.x+this.w/2.6, this.y+this.h/2.8)
      }

    
      p.text(this.mana, this.x-this.w/2.99, this.y-this.h/2.3)
     
      p.pop();

     
      p.push();
      p.fill(0);
      p.textSize(smaller_font_size);
      let translation_offset_y;
      if(this.oversized){
          translation_offset_y = this.y - this.h/2 + 80;
          p.translate(this.x, this.y - this.h/2 + 80);
      } else {
          translation_offset_y = this.y  + 50;
          p.translate(this.x, this.y + 50);
      }
      
      this.mouse_over_card_effect = false;
      this.hovered_effect = null;
      for(let e of this.effects){
          
          translation_offset_y += e.effect_string_height/2;
          p.translate(0, e.effect_string_height/2)

          if(p.mouseY > translation_offset_y - e.effect_string_height/2 &&
            p.mouseY < translation_offset_y + e.effect_string_height/2 &&
            p.mouseX > this.x - e.effect_string_width/2 &&
            p.mouseX < this.x + e.effect_string_width/2){

              this.mouse_over_card_effect = true;

              this.hovered_effect = e;
              this.hovered_effect.x = this.x - e.effect_string_width/2;
              this.hovered_effect.y = translation_offset_y - e.effect_string_height;
              p.fill(0, 100);
          } else {
              p.fill(0, 50)
          }

          p.rect(0, 0, e.effect_string_width, e.effect_string_height, 4, 4)
          p.fill(255, 255)
          p.text(e.effect_string, 0, 0, blank_spell_img.width/2, blank_spell_img.height/2)
          translation_offset_y += e.effect_string_height/2+5;
          p.translate(0, e.effect_string_height/2+5)

      }
      p.pop();


      p.push();

      if(editing_card == this){
          if(editing == "mana"){
              editX = this.x-this.w/2.99;
              editY = this.y-this.h/2.3;
          } else if(editing == "power"){
              editX = this.x-this.w/2.99;
              editY = this.y+this.h/2.8;
          } else if(editing == "toughness"){
              editX = this.x+this.w/2.6;
              editY = this.y+this.h/2.8;
          } 
      }

      p.pop();
  }


  mouseInImg(){
      return (p.mouseX > this.x - this.w / 2 - mouse_padding &&
        p.mouseX < this.x + this.w / 2 + mouse_padding &&
        p.mouseY > this.y - this.h / 2 - mouse_padding &&
        p.mouseY < this.y + this.h / 2 + mouse_padding);

  }
  check_mouse_hovers(){
      if (card_types[this.type_id] == "minion") {
          this.mouse_over_power = p.dist(p.mouseX, p.mouseY, this.x-this.w/2.99, this.y+this.h/2.8) < 50
          this.mouse_over_toughness = p.dist(p.mouseX, p.mouseY, this.x+this.w/2.6, this.y+this.h/2.8) < 50
      }
      this.mouse_over_mana = p.dist(p.mouseX, p.mouseY, this.x-this.w/2.99, this.y-this.h/2.3) < 50
  }
}





p.Button = class {

  constructor(button_name, button_id){
    this.button_name = button_name;
    this.button_id = button_id;

    this.x = 0;
    this.y = 0;
    this.w = p.textWidth(button_name) + 14;
    this.h = font_pixels + 10;
    this.fillAlpha = 100;

    this.text_x = 0;
    this.text_y = 0;
  }
  mouseInRegion(){
    return (p.mouseX > this.x - this.w / 2 - mouse_padding &&
      p.mouseX < this.x + this.w / 2 + mouse_padding &&
      p.mouseY > this.y - this.h / 2 - mouse_padding &&
      p.mouseY < this.y + this.h / 2 + mouse_padding);
  }

  resized(){
    this.x = w_padding - 150 + this.w / 2 - 7;
    this.y = p.map(this.button_id, 0, buttons.length, h_padding, p.height - h_padding);
    this.text_x = this.x - this.w / 2 + 7;
    this.text_y = this.y - 6;
  }

  run(){
    this.update();
    this.display();
  }

  update(){

    if (this.mouseInRegion() && current_survey_topic == 0) {
      this.fillAlpha = 255;
    } else {
      this.fillAlpha = 100;
    }

  }

  display(){


    p.textSize(font_pixels)
    p.textAlign(p.LEFT, p.CENTER)
    p.fill(255, this.fillAlpha);
    p.rect(this.x, this.y, this.w, this.h, 4, 4);
    p.fill(0, 255);
    p.text(this.button_name, this.text_x, this.text_y);
  }

  
}


document.oncontextmenu = function() {
  return false;
}


}