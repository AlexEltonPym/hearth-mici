/* eslint eqeqeq: "off", no-unused-vars: "off" */


//to fix totalHeight bug, change p5 by changing o-totalHeight to just o
//todo: fix this on a generic p5 import somehow


//todo: language stuff
//todo: buttons
//todo: creature types
//todo: card types
//todo: effect limit
//ABC test reports, articulate logic for report design

//make rampiness, variety, controllynes and see when they would be useful

export default function sketch(p) {


  const buttons = [];
  let button_id = 1;

  const effects = [];


  let current_task_index = 0;
  const task_details = [{
    id: 0,
    title: "3 Hunter Cards",
    instruction: "Design three cards for hunter",
    num_cards: 3,
    class: "hunter"
  },
  {
    id: 1,
    title: "3 Warrior Cards",
    instruction: "Design three cards for warrior",
    num_cards: 3,
    class: "warrior"
  },
  {
    id: 2,
    title: "3 Mage Cards",
    instruction: "Design three cards for mage",
    num_cards: 3,
    class: "mage"
  },
  // {
  //   id: 3,
  //   title: "3 Neutral Cards",
  //   instruction: "Design three neutral cards",
  //   num_cards: 3,
  //   class: "all"
  // }
  ]



  let user = ""
  let username = ""
  let report_enabled = false
  let report_array = []

  let tasks = [];
  const card_types = ["spell", "minion", "weapon"]

  const method_names = ["randomly", "targeted", "all"];
  const target_names = ["minions", "heroes", "minions or heroes", "pirates", "beasts", "elementals", "totems", "weapons"];
  const target_names_singular = ["minion", "hero", "minion or hero", "pirate", "beast", "elemental", "totem", "weapon"]
  const filter_names = ["enemy", "friendly", "all"];
  const duration_names = ["turn", "permanently"];
  const param_format_names = ["x", "x/x", "k", "c"];
  const effect_names = ["Deal damage", "Destroy", "Restore health", "Gain armour", "Change stats", "Set stats", "Give keyword", "Return to hand", "Draw", "Gain mana", "Summon: ", "Battlecry: ", "Deathrattle: "]
  const keywords = ["Taunt", "Charge", "Lifesteal", "Spell damage +1", "Divine shield", "Poisonous", "Windfury", "Frozen"]
  const all_creature_types = ["pirate", "beast", "elemental", "totem", "dragon", "pirate", "mech", "elemental"]
  const creature_types = ["Pirate", "Beast", "Elemental", "Totem"]

  const survey_topics = ["none", "methods", "filters", "targets", "duration", "params"];
  let current_survey_topic = 0;

  let survey_drop_target = null;

  let font_pixels_large = 32;
  let font_pixels = 24;
  let font_pixels_small = 20;
  let font_pixels_extra_small = 14;

  let hearthstone_font;
  const mouse_padding = 1;
  let w_padding, h_padding;
  let grid_w_padding, grid_h_padding;

  let rect_mask, ellipse_mask;
  let blank_spell_img, blank_creature_img, blank_weapon_img, full_blank_creature_img;
  let bg;
  let gan_imgs = [];


  let the_mouse;
  let setup_done = false;
  let hovered_option = -1;

  let editing = "none";
  let editing_card = null;
  let effect_to_remove = null;
  let editX = 0;
  let editY = 0;

  let sending = false;
  let send_start_time = -10000;
  const estimated_send_duration = 3000; //over-estimate
  let sent = false;

  let mouse_over_queuer;
  let mouse_over_next;
  let mouse_over_prev;


  let props;

  let report;


  p.myCustomRedrawAccordingToNewPropsHandler = (_props) => {
    props = _props;
  }

  p.preload = () => {
    bg = p.loadImage(props.bg_img)
    blank_spell_img = p.loadImage(props.spell_img);
    blank_weapon_img = p.loadImage(props.weapon_img)
    blank_creature_img = p.loadImage(props.creature_img)
    full_blank_creature_img = p.loadImage(props.full_blank_creature_img);
    hearthstone_font = p.loadFont(props.hs_font);
    for (let im of props.gan_imgs) {
      gan_imgs.push(p.loadImage(im))
    }
    report = props.report
  }


  p.setup = () => {
    p.createCanvas(p.windowWidth, p.windowHeight);
    user = p.getURLParams().user ?? 2;
    report_enabled = (p.getURLParams().report ?? false) === "true";
    username = p.convertUserToName(user)
    for(let report_key in report){
      if(report_key.split("_")[0] == username){
        report_array.push(Object.values(report[report_key]))
      }
    }
   
    the_mouse = new p.FancyMouse();


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


    for (let task of task_details) {
      tasks[task.id] = [];
      for (let card_id = 0; card_id < task.num_cards; card_id++) {
        tasks[task.id].push(new p.Card(card_id, task.id, task.class));
      }
    }

    p.load_save(); //loads save file from google sheets if it exists

    p.resize_all();



    setup_done = true;

  }


  p.draw = () => {
    p.resize_all();
    p.background(255)
    p.textAlign(p.LEFT, p.CENTER);
    p.image(bg, p.width / 2, p.height / 2, p.width, p.height);


    if (current_task_index < task_details.length) {
      for (let c of tasks[current_task_index]) {
        c.run();
      }
    

    for (let b of buttons) {
      b.run();
    }
  
    p.textSize(font_pixels+4)
    p.text("Base attributes:", report_enabled?w_padding/4:w_padding/2, h_padding)
    p.text("Battlecrys:",report_enabled?w_padding/4:w_padding/2, p.map(3, 0, 16, h_padding, p.height - h_padding))
  }


    if (the_mouse.busy && current_survey_topic == 0) {
      p.push();
      p.translate(p.mouseX - the_mouse.xOffset, p.mouseY - the_mouse.yOffset)
      p.textSize(28)
      p.text(the_mouse.effect.label_name, 0, 0)
      p.pop();
    }

    p.draw_edit_overlay();
    p.draw_task_controls();


    if (current_task_index == task_details.length) {
      p.send_overlay();
    } else {
      p.draw_task_overlay();

    }


    if (survey_topics[current_survey_topic] != "none") {
      p.draw_survey();
    }

  }

  p.draw_task_controls = () => {


    let next_x = p.width - w_padding;
    let next_y = p.height - (report_enabled?h_padding/2:h_padding);
    mouse_over_next = p.dist(p.mouseX, p.mouseY, next_x, next_y) < 75;

    p.push();
    p.translate(next_x, next_y)
    p.fill(255, current_task_index == task_details.length ? 0 : mouse_over_next ? 255 : 100)
    p.triangle(0, -25, 0, 25, 75, 0);
    p.pop();

    let prev_x = p.map(1, 0, 3, w_padding, p.width - w_padding)
    mouse_over_prev = p.dist(p.mouseX, p.mouseY, prev_x, next_y) < 75;

    p.push();
    p.translate(prev_x, next_y)
    p.fill(255, current_task_index == 0 ? 50 : mouse_over_prev ? 255 : 100)
    p.triangle(0, -25, 0, 25, -75, 0);
    p.pop();

  }

  p.draw_task_overlay = () => {
    p.textAlign(p.RIGHT, p.CENTER)
    p.textSize(font_pixels);
    p.text(task_details[current_task_index].instruction, p.width - w_padding / 2, report_enabled?h_padding/2:h_padding)


    p.fill(0);
    p.textAlign(p.CENTER, p.CENTER);
    p.text(`Task ${current_task_index + 1} \\ ${task_details.length}`, p.map(2, 0, 3, w_padding, p.width - w_padding), p.height - (report_enabled?h_padding/2:h_padding))
  }



  p.draw_survey = () => {
    p.push();
    p.textAlign(p.CENTER, p.CENTER)
    p.textSize(font_pixels)

    p.rectMode(p.CENTER)
    p.background(0, 100)

    let setting = the_mouse.effect.settings[survey_topics[current_survey_topic]]
    let options = setting[0]


    if (setting[0][0] == "x") {
      options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    } else if (setting[0][0] == "k") {
      options = keywords
    } else if (setting[0][0] == "c") {
      options = creature_types;
    }


    if (options[0] == "x/x") {
      for (let attack = 0; attack <= 10; attack++) {
        for (let defense = 0; defense <= 10; defense++) {
          let xPos = p.map(attack, 0, 10, grid_w_padding, p.width - grid_w_padding);
          let yPos = p.map(defense, 0, 10, grid_h_padding, p.height - grid_h_padding);
          let box_width = (p.width - grid_w_padding * 2) / 10;
          let box_height = (p.height - grid_h_padding * 2) / 10;

          if (p.mouseX > xPos - box_width / 2 && p.mouseX < xPos + box_width / 2 &&
            p.mouseY > yPos - box_height / 2 && p.mouseY < yPos + box_height / 2) {
            p.fill(255, 100);
          } else {
            p.fill(255, 0);
          }
          p.rect(xPos, yPos, box_width, box_height);
          p.fill(255);
          p.text(attack + "/" + defense, xPos, yPos - 10)
        }
      }
    } else {


      p.textSize(40);
      p.fill(255)
      p.text(the_mouse.effect.label_name + "...", p.width / 2, p.height * 0.1);

      p.textSize(font_pixels)
      p.rectMode(p.CENTER)

      let option_button_width = (p.width / options.length) * 0.5;
      let option_button_height = p.height * 0.10;
      let option_buttons_padding = p.width * 0.25;

      for (let [index, option] of options.entries()) {
        let xPos = p.map(index, 0, options.length - 1, option_buttons_padding, p.width - option_buttons_padding);
        if (p.mouseX > xPos - option_button_width / 2 && p.mouseX < xPos + option_button_width / 2) {
          p.fill(255, 100)
          hovered_option = index;
        } else {
          p.fill(255, 50)
        }
        p.rect(xPos, p.height * 0.5, option_button_width, option_button_height, 16);
        p.fill(255);

        let option_string = option.toString();
        option_string = option_string[0].toUpperCase() + option_string.substring(1)
        option_string = option_string.split(" ").join("\n");

        p.text(option_string, xPos, p.height / 2)
      }
    }

    p.pop();
  }


  p.mouse_pressed_while_surveying = () => {
    if (p.progress_survey_through_issues()) {
      return
    }


    let setting = the_mouse.effect.settings[survey_topics[current_survey_topic]];
    let options = setting[0]
    if (options[0] == "x") {
      options = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    } else if (options[0] == "k") {
      options = keywords;
    } else if (options[0] == "c") {
      options = creature_types;
    }

    if (options[0] == "x/x") {
      let selectedAttack = 0;
      let selectedDefense = 0;
      for (let attack = 0; attack <= 10; attack++) {
        for (let defense = 0; defense <= 10; defense++) {
          let xPos = p.map(attack, 0, 10, grid_w_padding, p.width - grid_w_padding);
          let yPos = p.map(defense, 0, 10, grid_h_padding, p.height - grid_h_padding);
          let box_width = (p.width - grid_w_padding * 2) / 10;
          let box_height = (p.height - grid_h_padding * 2) / 10;

          if (p.mouseX > xPos - box_width / 2 && p.mouseX < xPos + box_width / 2 &&
            p.mouseY > yPos - box_height / 2 && p.mouseY < yPos + box_height / 2) {
              selectedAttack = attack;
              selectedDefense = defense;
              break;
            }
          }
        }

      setting[1] = `${selectedAttack}/${selectedDefense}`;
    } else {
      setting[1] = options[hovered_option]
    }



    current_survey_topic++;

    if (p.progress_survey_through_issues()) {
      return
    }

  }


  p.mouse_pressed_while_not_surveying = () => {
    let clicked_card = null;

    if (current_task_index < task_details.length) {
      for (let c of tasks[current_task_index]) {
        if (c.mouseInImg()) {
          clicked_card = c;
        }
      }
    }


    if (clicked_card) {
      if (the_mouse.busy) { //dropping effect onto a card
        p.drop_effect_on_card(clicked_card)
      } else { //clicking on a card generally
        p.click_to_edit_card(clicked_card)
      }
    } else {
      if (the_mouse.busy) { //clicked away to drop label
        the_mouse.busy = false;
        the_mouse.setOffset(0, 0);
        the_mouse.effect = null;
      } else { //other clicks


        if (mouse_over_next && current_task_index < task_details.length) {
          current_task_index++;
        } else if (mouse_over_prev && current_task_index > 0) {
          current_task_index--;
        }

        if (mouse_over_queuer && current_task_index == task_details.length && !sending) {
          p.submit();
        }

        p.mouse_click_while_editing();


        for (let b of buttons) { //clicking on a button with an empty hand
          if (b.mouseInRegion()) {
            the_mouse.busy = true;
            the_mouse.setOffset(b.text_x, b.text_y);
            the_mouse.effect = JSON.parse(JSON.stringify(effects[b.button_name]));

            break;
          }
        }
      }
    }

  }



  //returns true if you need to return out of mouse
  p.progress_survey_through_issues = () => {
    if (current_survey_topic == survey_topics.length) {
      p.finished_survey();
      return true;
    }

    for (let i = 0; i < survey_topics.length; i++) {
      if (the_mouse.effect.settings[survey_topics[current_survey_topic]][0] == null ||
        (!param_format_names.includes(the_mouse.effect.settings[survey_topics[current_survey_topic]][0][0]) &&
          the_mouse.effect.settings[survey_topics[current_survey_topic]][0].length == 1)) {
        current_survey_topic++;
        if (current_survey_topic == survey_topics.length) {
          p.finished_survey();
          return true;
        }
      }
    }


    if (current_survey_topic == survey_topics.length) {
      p.finished_survey();
      return true;
    }


    return false;
  }

  p.drop_effect_on_card = (c) => {
    current_survey_topic = 1;
    survey_drop_target = c;

    if (p.progress_survey_through_issues()) {

      return
    }
  }


  p.click_to_edit_card = (c) => {

    if (c.mouse_over_mana) {
      editing = "mana";
      editing_card = c;
    } else if (c.mouse_over_power) {
      editing = "power";
      editing_card = c;
    } else if (c.mouse_over_toughness && !(editing == "effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10)) {
      editing = "toughness";
      editing_card = c;
    } else if (c.mouse_over_card_effect && !(editing == "effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10)) {
      editing = "effect";
      editX = c.hovered_effect.x + blank_spell_img.width * p.min(p.width*0.0005, 0.75)*0.75;
      editY = c.hovered_effect.y + c.hovered_effect.effect_string_height / 2;
      editing_card = c;
      effect_to_remove = c.hovered_effect;
    } else if (editing == "effect" && p.dist(p.mouseX, p.mouseY, editX, editY) < 10) {
      editing_card.effects.splice(editing_card.effects.indexOf(effect_to_remove), 1);
      editing = "none";
    } else {
      editing = "none";
    }
  }


  p.mouse_click_while_editing = () => {
    if (editing == "mana") {
      if (p.dist(p.mouseX, p.mouseY, editX - 60, editY - 50) < 40) {
        editing_card.mana--;
      } else if (p.dist(p.mouseX, p.mouseY, editX + 60, editY - 50) < 40) {
        editing_card.mana++;
      } else {
        editing = "none"
      }
      editing_card.mana = p.constrain(editing_card.mana, 0, 10)
    } else if (editing == "power") {

      if (p.dist(p.mouseX, p.mouseY, editX - 60, editY + 50) < 40) {
        editing_card.power--;
      } else if (p.dist(p.mouseX, p.mouseY, editX + 60, editY + 50) < 40) {
        editing_card.power++;
      } else {
        editing = "none"
      }
      editing_card.power = p.constrain(editing_card.power, 0, 10)
    } else if (editing == "toughness") {

      if (p.dist(p.mouseX, p.mouseY, editX - 60, editY + 50) < 40) {
        editing_card.toughness--;
      } else if (p.dist(p.mouseX, p.mouseY, editX + 60, editY + 50) < 40) {
        editing_card.toughness++;
      } else {
        editing = "none"
      }
      editing_card.toughness = p.constrain(editing_card.toughness, 1, 10)
    } else if (editing == "effect") {
      editing = "none";
    }
  }


  p.draw_edit_overlay = () => {
    p.push();
    if (editing != "none") {
      p.translate(editX, editY)
      p.noStroke();
      if (editing == "effect") {
        p.rotate(p.QUARTER_PI);
        p.fill(0);
        p.rect(0, 0, 22, 6);
        p.rect(0, 0, 6, 22);
        p.fill(255);
        p.rect(0, 0, 20, 4);
        p.rect(0, 0, 4, 20);

      } else {
        p.fill(0);
        p.rect(-60, editing == "mana" ? -50 : 75, 32, 8);
        p.rect(60, editing == "mana" ? -50 : 75, 32, 8);
        p.rect(60, editing == "mana" ? -50 : 75, 8, 32);
        p.fill(255);
        p.rect(-60, editing == "mana" ? -50 : 75, 30, 6);
        p.rect(60, editing == "mana" ? -50 : 75, 30, 6);
        p.rect(60, editing == "mana" ? -50 : 75, 6, 30);
      }
    }
    p.pop();
  }

  p.mousePressed = () => {
    if (setup_done) {
      if (survey_topics[current_survey_topic] != "none") {
        p.mouse_pressed_while_surveying();
      } else {
        p.mouse_pressed_while_not_surveying();
      }
    }
  }

  p.finished_survey = () => {

    survey_drop_target.effects.push(JSON.parse(JSON.stringify(the_mouse.effect)))
    current_survey_topic = 0;
    the_mouse.effect = null;
    the_mouse.busy = false;
  }

  p.keyPressed = () => {
    if(p.key == 'r'){
      report_enabled = !report_enabled
    }
  }

  p.windowResized = () => {
    p.resizeCanvas(p.windowWidth, p.windowHeight);
    p.resize_all();
  }

  p.ease_out_cubic = (x) => {
    return 1 - p.pow(1 - x, 3);
  }


  p.send_overlay = () => {

    p.text("Thank you for completing the tasks,\nPlease hit the button to save your responses.", p.width/2, p.height/2)
    p.push();
    let queur_x = p.width - w_padding;
    let queur_y = p.height - h_padding;
    mouse_over_queuer = (p.mouseX > queur_x - 100 && p.mouseX < queur_x + 100 && p.mouseY > queur_y - 30 && p.mouseY < queur_y + 30)

    p.translate(queur_x, queur_y);

    if (sending) {
      let q = p.map(p.millis(), send_start_time, send_start_time + estimated_send_duration, 0, 1, true)
      q = p.ease_out_cubic(q);

      p.fill(255, p.map(q, 0, 1, 50, 100));
      p.rect(p.map(q, 0, 1, -100, 0), 0, p.map(q, 0, 1, 0, 200), 60, 4);
      p.rect(0, 0, 200, 60, 4);
    } else {
      p.fill(255, mouse_over_queuer ? 255 : 100);
      p.rect(0, 0, 200, 60, 4)
    }



    p.fill(0, 255);
    p.textAlign(p.CENTER, p.CENTER)
    p.text(sending ? sent ? "Saving again..." : "Saving..." : sent ? mouse_over_queuer ? "Save again" : "Done." : "Save to system", 0, -4)
    p.pop();

  }

  p.submit = () => {
    if (!sending) {
      sending = true;
      send_start_time = p.millis();

      const submissions = p.generate_submissions();

      props.send_to_google_sheets(submissions).then((result) => {
        console.log(result);
        sending = false;
        sent = true;

      })
    }
  }

  p.load_save = () => {
    props.load_from_google_sheets(user).then((result) => {
      if(result.data.r){
        let loaded_save = result.data.r.data.values[0];
        if(loaded_save[2]){
          tasks = JSON.parse(loaded_save[2]);
          for(let t of tasks){
            for(let c of t){
              c.__proto__ = p.Card.prototype;
            }
          }
          p.resize_all();
        }
      } else {
        console.log(result.data.e)
      }
    });
  }

  p.make_save = () => {
    let asString = JSON.stringify(tasks)

    props.save_to_google_sheets([user, asString]).then((result) => {
      console.log(result);
    })
  }

  p.generate_submissions = () => {
    const submissions = [];
    p.make_save();

    for (let t of tasks) {
      for (let c of t) {
        let card_submission = {
          id: c.card_id,
          task: c.card_task_index,
          user: user,
          p: c.power,
          t: c.toughness,
          m: c.mana,
        }


        let repeat_checker = {};

        for (let e of c.effects) {
          if (repeat_checker[e.effect_short] == undefined) {
            repeat_checker[e.effect_short] = 0;
          } else {
            repeat_checker[e.effect_short]++;
          }

          if (e.settings.methods[0] != null) card_submission[e.effect_short + "-method-" + repeat_checker[e.effect_short]] = e.settings.methods[1];
          if (e.settings.params[0] != null) card_submission[e.effect_short + "-param-" + repeat_checker[e.effect_short]] = e.settings.params[1];
          if (e.settings.targets[0] != null) card_submission[e.effect_short + "-target-" + repeat_checker[e.effect_short]] = e.settings.targets[1];
          if (e.settings.filters[0] != null) card_submission[e.effect_short + "-filter-" + repeat_checker[e.effect_short]] = e.settings.filters[1];
          if (e.settings.duration[0] != null) card_submission[e.effect_short + "-duration-" + repeat_checker[e.effect_short]] = e.settings.duration[1];

        }
        submissions[c.card_task_index + "-" + c.card_id] = card_submission;
      }
    }

    return submissions;
  }

  p.resize_all = () => {
    
    h_padding = p.height * 0.1;
    w_padding = p.width * 0.2;
    grid_h_padding = p.height * 0.2;
    grid_w_padding = p.width * 0.1;

    font_pixels_large = p.min(p.width*32*0.0008, 32);
    font_pixels = p.min(p.width*24*0.0008, 24);
    font_pixels_small = p.min(p.width*20*0.0008, 20);

    for (let b of buttons) {
      b.resized();
    }

    for (let t of tasks) {
      for (let c of t) {
        c.resized();
        
      }
    }

    for(let e of effects){
      e.resized();
    }

    p.generate_masks();

  }

  p.generate_masks = () => {
    ellipse_mask = p.createGraphics(250, 250);
    ellipse_mask.ellipse(ellipse_mask.width / 2, ellipse_mask.height / 2, 200, 200)

    rect_mask = p.createGraphics(250, 250);
    rect_mask.rectMode(p.CENTER);
    rect_mask.rect(rect_mask.width / 2, rect_mask.height / 2, 200, 160)
  }

  p.register_effect = (effect_text, effect_short, method, param, targets, filters, duration) => {

    effects[effect_text] = new p.Effect(effect_text, effect_short, method, param, targets, filters, duration);
    buttons.push(new p.Button(effect_text, button_id++));
    if(button_id == 3){
      button_id++;
    }
  }

  p.register_all = () => {

   

    p.register_effect("Keywords", "key",
      null,
      ["k"],
      null,
      null,
      null);

    p.register_effect("Creature types", "cre",
      null,
      ["c"],
      null,
      null,
      null);
      p.register_effect("Set stats", "set",
      ["randomly", "targeted", "all"],
      ["x/x"],
      ["minions", "pirates", "beasts", "elementals", "totems"],
      ["enemy", "friendly", "all"],
      ["turn", "permanently"]);

    p.register_effect("Give stats", "cha",
      ["randomly", "targeted", "all"],
      ["x/x"],
      ["minions", "pirates", "beasts", "elementals", "totems"],
      ["enemy", "friendly", "all"],
      ["turn", "permanently"]);


    

    p.register_effect("Draw cards", "dra",
    null,
    ["x"],
    null,
    ["enemy", "friendly", "all"],
    null);

   
    p.register_effect("Deal damage", "dam",
      ["randomly", "targeted", "all"],
      ["x"],
      ["minions", "heroes", "minions or heroes", "pirates", "beasts", "elementals", "totems"],
      ["enemy", "friendly", "all"],
      null);
      
      p.register_effect("Gain armour", "arm",
      null,
      ["x"],
      null,
      ["enemy", "friendly", "all"],
      null);

      p.register_effect("Give keyword", "giv",
      ["randomly", "targeted", "all"],
      ["k"],
      ["minions", "pirates", "beasts", "elementals", "totems"],
      ["enemy", "friendly", "all"],
      ["turn", "permanently"]);

      p.register_effect("Restore health", "hea",
      ["randomly", "targeted", "all"],
      ["x"],
      ["minions", "heroes", "minions or heroes", "pirates", "beasts", "elementals", "totems"],
      ["enemy", "friendly", "all"],
      null);
    p.register_effect("Return to hand", "ret",
    ["randomly", "targeted", "all"],
    null,
    ["minions", "pirates", "beasts", "elementals", "totems"],
    ["enemy", "friendly", "all"],
    null);



  p.register_effect("Summon token", "sum",
  null,
  ["x/x"],
  null,
  null,
  null);
    p.register_effect("Destroy minions", "des",
      ["randomly", "targeted", "all"],
      null,
      ["minions", "pirates", "beasts", "elementals", "totems", "weapons"],
      ["enemy", "friendly", "all"],
      null);

    





  p.register_effect("Gain mana crystals", "gai",
    null,
    ["x"],
    null,
    ["enemy", "friendly", "all"],
    null);


   



  }


  p.FancyMouse = class {
    constuctor() {
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
    constructor(label_name, effect_short, methods, param_format, targets, filters, duration) {
      this.x = 0;
      this.y = 0;

      this.effect_string = "";
      this.effect_string_height = 0;
      this.effect_string_width = blank_spell_img.width * p.min(p.width*0.0005, 0.75)/2;
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
    constructor(card_id, card_task_index, card_class) {
      this.y = 0;
      this.x = 0;
      this.w = blank_spell_img.width * 0.75;
      this.h = blank_spell_img.height * 0.75;
      this.oversized = false;


      this.class = card_class;
      this.type_id = 1; //creature
      this.card_id = card_id;
      this.card_task_index = card_task_index;


      this.flav_img_index = p.floor(p.random(gan_imgs.length));
      this.mana = 5;
      this.power = 5;
      this.toughness = 5;
      this.effects = [];

      this.hovered_effect = null;
      this.mouse_over_card_effect = false;
      this.mouse_over_mana = false;
      this.mouse_over_power = false;
      this.mouse_over_toughness = false;


    }

    resized() {
      if (tasks[this.card_task_index].length == 1) {
        this.x = p.map(2, 0, 3, w_padding, p.width - w_padding)
      } else if (tasks[this.card_task_index].length == 2) {
        this.x = p.map(this.card_id == 0 ? 1.5 : 2.5, 0, 3, w_padding, p.width - w_padding)
      } else {
        this.x = p.map(this.card_id + 1, 0, 3, report_enabled?w_padding/2:w_padding, p.width - w_padding)
      }
      this.y = report_enabled?p.height / 3:p.height/2;
      this.w = blank_spell_img.width * p.min(p.width*0.0005, 0.75);
      this.h = blank_spell_img.height * p.min(p.width*0.0005, 0.75);

      for(let e of this.effects){
        e.effect_string_width = blank_spell_img.width * p.min(p.width*0.0005, 0.75)*0.75;
        p.textSize(font_pixels_small)
        let num_lines = p.textWidth(e.effect_string)/e.effect_string_width;
        e.effect_string_height = font_pixels_small * p.ceil(num_lines) + font_pixels_small;
      }
    }

    run() {
      this.generate_effect_text();
      this.check_mouse_hovers();
      this.display();
    }

    generate_effect_text() {
      for (let e of this.effects) {
        e.effect_string = "";
        if (e.label_name == "Keywords" || e.label_name == "Creature types") {
          e.effect_string = e.settings.params[1];
        } else if (e.label_name == "Deal damage") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Deal " + e.settings.params[1] + " damage to a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Deal " + e.settings.params[1] + " damage to target ";
          } else {
            e.effect_string = "Battlecry: Deal " + e.settings.params[1] + " damage to all "
          }

          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
        } else if (e.label_name == "Destroy minions") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Destroy a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Destroy a target ";
          } else {
            e.effect_string = "Battlecry: Destroy all "
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
        } else if (e.label_name == "Restore health") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Restore " + e.settings.params[1] + " health to a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Restore " + e.settings.params[1] + " health to a target ";
          } else {
            e.effect_string = "Battlecry: Restore " + e.settings.params[1] + " health to all ";
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
        } else if (e.label_name == "Draw cards") {
          if (e.settings.filters[1] == "enemy") {
            e.effect_string = "Battlecry: Enemy draws " + e.settings.params[1] + " cards";
          } else if (e.settings.filters[1] == "friendly") {
            e.effect_string = "Battlecry: Draw " + e.settings.params[1] + " cards";
          } else {
            e.effect_string = "Battlecry: Both players draw " + e.settings.params[1] + " cards";
          }       
        } else if (e.label_name == "Gain armour") {
          if (e.settings.filters[1] == "enemy") {
            e.effect_string = "Battlecry: Enemy gains " + e.settings.params[1] + " armour";
          } else if (e.settings.filters[1] == "friendly") {
            e.effect_string = "Battlecry: Gain " + e.settings.params[1] + " armour";
          } else {
            e.effect_string = "Battlecry: Both players gain " + e.settings.params[1] + " armour";
          }       
         } else if (e.label_name == "Return to hand") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Return a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Return a target ";
          } else {
            e.effect_string = "Battlecry: Return all "
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
          e.effect_string += " to their owners hand."
        } else if (e.label_name == "Summon token") {
          e.effect_string = "Battlecry: Summon a " + e.settings.params[1] + " minion";
        } else if (e.label_name == "Gain mana crystals") {
          if (e.settings.filters[1] == "enemy") {
            e.effect_string = "Battlecry: Enemy gains " + e.settings.params[1] + " mana crystals";
          } else if (e.settings.filters[1] == "friendly") {
            e.effect_string = "Battlecry: Gain " + e.settings.params[1] + " mana crystals";
          } else {
            e.effect_string = "Battlecry: Both players gain " + e.settings.params[1] + " empty mana crystals";
          }       
        } else if (e.label_name == "Set stats") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Set a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Set a target ";
          } else {
            e.effect_string = "Battlecry: Set all "
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
          e.effect_string += " to " + e.settings.params[1]
          if(e.settings.duration == "turn"){
            e.effect_string += " for this turn"
          } else {
            e.effect_string += " permanently"

          }
        } else if (e.label_name == "Give stats") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Give a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Give a target ";
          } else {
            e.effect_string = "Battlecry: Give all "
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
          e.effect_string += " +"+e.settings.params[1].split("/")[0]+"/+"+e.settings.params[1].split("/")[1]
          if(e.settings.duration == "turn"){
            e.effect_string += " for this turn"
          } else {
            e.effect_string += " permanently"

          }
        } else if (e.label_name == "Give keyword") {
          if (e.settings.methods[1] == "randomly") {
            e.effect_string = "Battlecry: Give a random ";
          } else if (e.settings.methods[1] == "targeted") {
            e.effect_string = "Battlecry: Give a target ";
          } else {
            e.effect_string = "Battlecry: Give all "
          }
          e.effect_string += e.settings.filters[1] == "all" ? "" : e.settings.filters[1] + " " //remove "all all"
          if (e.settings.methods[1] == "all") {
            e.effect_string += e.settings.targets[1]
          } else {
            e.effect_string += target_names_singular[target_names.indexOf(e.settings.targets[1])]
          }
          e.effect_string += " "+e.settings.params[1].toLowerCase()
          if(e.settings.duration == "turn"){
            e.effect_string += " for this turn"
          } else {
            e.effect_string += " permanently"

          }
        } else {
          e.effect_string = e.label_name
        }


        p.textSize(font_pixels_small)
        let num_lines = (p.textWidth(e.effect_string)+150)/e.effect_string_width;
        e.effect_string_height = font_pixels_small * p.ceil(num_lines) + font_pixels_small;

      }

    }

    display() {
      p.push();

      p.fill(0);
      p.textAlign(p.CENTER, p.CENTER)
      if (this.effects.length > 1) {
        this.oversized = true;
      } else {
        this.oversized = false;
      }


      let flav = gan_imgs[this.flav_img_index].get();
      let forg;

      if (card_types[this.type_id] == "spell") {
        flav.mask(rect_mask)
        forg = blank_spell_img;
      } else if (card_types[this.type_id] == "minion") {
        flav.mask(ellipse_mask)
        forg = this.oversized ? full_blank_creature_img : blank_creature_img;
      } else {
        flav.mask(rect_mask)
        forg = blank_weapon_img;
      }

      if (!this.oversized) {
        p.image(flav, this.x, this.y - this.h*0.20, this.w*0.7, this.h*0.7)
      }
      
      p.image(forg, this.x, this.y, this.w, this.h);

      p.push();
      p.textSize(font_pixels_large*2);
      p.fill(255);
      p.strokeWeight(3);
      p.stroke(0);

      if (card_types[this.type_id] == "minion") {
        p.text(this.power, this.x - this.w / 2.99, this.y + this.h / 2.8)
        p.text(this.toughness, this.x + this.w / 2.6, this.y + this.h / 2.8)
      }


      p.text(this.mana, this.x - this.w / 2.99, this.y - this.h / 2.3)

      p.pop();


      p.push();
      p.fill(0);
      let translation_offset_y;
      if (this.oversized) {
        translation_offset_y = this.y - this.h *0.3;
        p.translate(this.x, this.y - this.h * 0.3);
      } else {
        translation_offset_y = this.y + this.h*0.1;
        p.translate(this.x, this.y + this.h*0.1);
      }

      this.mouse_over_card_effect = false;
      this.hovered_effect = null;

      for (let e of this.effects) {

        translation_offset_y += e.effect_string_height / 2;
        p.translate(0, e.effect_string_height / 2)

        if (p.mouseY > translation_offset_y - e.effect_string_height / 2 &&
          p.mouseY < translation_offset_y + e.effect_string_height / 2 &&
          p.mouseX > this.x - e.effect_string_width / 2 &&
          p.mouseX < this.x + e.effect_string_width / 2) {

          this.mouse_over_card_effect = true;

          this.hovered_effect = e;
          this.hovered_effect.x = this.x - e.effect_string_width / 2;
          this.hovered_effect.y = translation_offset_y - e.effect_string_height;
          p.fill(0, 100);
        } else {
          p.fill(0, 50)
        }
        p.rect(0, 0, e.effect_string_width, e.effect_string_height, 4, 4)
        p.fill(255, 255)
        p.textSize(font_pixels_small)

        p.textAlign(p.LEFT, p.TOP)
        p.text(e.effect_string, 0, 0, e.effect_string_width, e.effect_string_height)
        translation_offset_y += e.effect_string_height / 2 + 5;
        p.translate(0, e.effect_string_height / 2 + 5)

      }
      p.pop();


      p.push();

      if (editing_card == this) {
        if (editing == "mana") {
          editX = this.x - this.w / 2.99;
          editY = this.y - this.h / 2.3;
        } else if (editing == "power") {
          editX = this.x - this.w / 2.99;
          editY = this.y + this.h / 2.8;
        } else if (editing == "toughness") {
          editX = this.x + this.w / 2.6;
          editY = this.y + this.h / 2.8;
        }
      }

      p.pop();
      p.pop();

      if(report_enabled && report_array.length > 0){
        let card_number = this.card_task_index * 3 + this.card_id
        if(card_number < report_array.length/3){


          let report_stats = report_array[card_number*3].concat(report_array[card_number*3+1]).concat(report_array[card_number*3+2])
          report_stats = report_stats.sort((a, b) => a[0] == 'WIN_RATE'?-1:b[0]=='WIN_RATE'?1:(a[5]-b[5]))
          console.log(report_stats)
          report_stats = report_stats.slice(0, 6)

          let mage_stats = []
          let hunter_stats = []
          let warrior_stats = []
          for(let stat of report_stats){
            if(stat[2] == "MAGE_DECK" || stat[2] == "MAGE_DECK_MIRROR"){
              mage_stats.push(stat);
            } else if(stat[2] == "HUNTER_DECK" || stat[2] == "HUNTER_DECK_MIRROR"){
              hunter_stats.push(stat);
            } else {
              warrior_stats.push(stat);
            }
          }

          p.textAlign(p.LEFT, p.TOP)
  

          let mage_padding = 0;
          let str = "Versus Mage:\n"
          p.textSize(font_pixels_small)
          p.text(str, this.x-this.w/2.5, this.y+this.h/2)
          str = ""
          for(let stat of mage_stats){
            let change = ((stat[4]-stat[3])/stat[3]*100).toFixed(0)
            str+=this.convertStatToName(stat[0]) + ": " + stat[3].toFixed(2) + "   > " + stat[4].toFixed(2) + " ("+ (change>0?"+":"") + change +"%)" + "\n"
            mage_padding++;
          }
          p.textSize(font_pixels_extra_small)
          p.text(str, this.x-this.w/2.5, this.y+this.h/2+font_pixels_small)

          let hunter_padding = 0;
          str = "Versus Hunter:\n"
          p.textSize(font_pixels_small)
          p.text(str, this.x-this.w/2.5, this.y+this.h/2+font_pixels_small*2+font_pixels_extra_small*mage_padding)
          str = ""

          for(let stat of hunter_stats){
            let change = ((stat[4]-stat[3])/stat[3]*100).toFixed(0)
            str+=this.convertStatToName(stat[0]) + ": " + stat[3].toFixed(2) + "   > " + stat[4].toFixed(2) + " ("+ (change>0?"+":"") + change +"%)" + "\n"
            hunter_padding++;
          }
          p.textSize(font_pixels_extra_small)
          p.text(str, this.x-this.w/2.5, this.y+this.h/2+font_pixels_small*3+font_pixels_extra_small*mage_padding)


          str = "Versus Warrior:\n"
          p.textSize(font_pixels_small)

          p.text(str, this.x-this.w/2.5, this.y+this.h/2+font_pixels_small*4+font_pixels_extra_small*(mage_padding+hunter_padding))
          str = ""

          for(let stat of warrior_stats){
            let change = ((stat[4]-stat[3])/stat[3]*100).toFixed(0)

            str+=this.convertStatToName(stat[0]) + ": " + stat[3].toFixed(2) + "   > " + stat[4].toFixed(2) + " ("+ (change>0?"+":"") + change +"%)" + "\n"
          }
          p.textSize(font_pixels_extra_small)

          p.text(str, this.x-this.w/2.5, this.y+this.h/2+font_pixels_small*5+font_pixels_extra_small*(mage_padding+hunter_padding))

       }
      }
    }

    convertStatToName(stat){
      let conversionMap = {
        'WIN_RATE': 'Winrate',
        'DAMAGE_DEALT': 'Damage dealt',
        'HEALING_DONE': 'Healing done',
        'MANA_SPENT': 'Mana spent',
        'CARDS_PLAYED': 'Cards played',
        'TURNS_TAKEN': 'Turns taken',
        'ARMOR_GAINED': 'Armor gained',
        'CARDS_DRAWN': 'Cards drawn',
        'FATIGUE_DAMAGE': 'Fatigue damage',
        'MINIONS_PLAYED': 'Minions played',
        'SPELLS_CAST': 'Spells cast',
        'HERO_POWER_USED': 'Hero power used',
        'WEAPONS_EQUIPPED': 'Weapons equipped',
        'WEAPONS_PLAYED': 'Weapons played',
        'CARDS_DISCARDED': 'Cards discarded',
        'HERO_POWER_DAMAGE_DEALT': 'Hero power damage',
        'ARMOR_LOST': 'Armor lost'
      }
     return conversionMap[stat]
    }



    mouseInImg() {
      return (p.mouseX > this.x - this.w / 2 - mouse_padding &&
        p.mouseX < this.x + this.w / 2 + mouse_padding &&
        p.mouseY > this.y - this.h / 2 - mouse_padding &&
        p.mouseY < this.y + this.h / 2 + mouse_padding);

    }
    check_mouse_hovers() {
      if (card_types[this.type_id] == "minion") {
        this.mouse_over_power = p.dist(p.mouseX, p.mouseY, this.x - this.w / 2.99, this.y + this.h / 2.8) < 50
        this.mouse_over_toughness = p.dist(p.mouseX, p.mouseY, this.x + this.w / 2.6, this.y + this.h / 2.8) < 50
      }
      this.mouse_over_mana = p.dist(p.mouseX, p.mouseY, this.x - this.w / 2.99, this.y - this.h / 2.3) < 50
    }
  }


  p.convertUserToName = (user) => {
    let conversionMap = {
      "2": "noUser",
      "3": "kaz",
      "4": "marcus",
      "5": "alex",
      "6": "liam",
      "10": "patrick"
    }
   return conversionMap[user]
  }



  p.Button = class {

    constructor(button_name, button_id) {
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
    mouseInRegion() {
      return (p.mouseX > this.x - this.w / 2 - mouse_padding &&
        p.mouseX < this.x + this.w / 2 + mouse_padding &&
        p.mouseY > this.y - this.h / 2 - mouse_padding &&
        p.mouseY < this.y + this.h / 2 + mouse_padding);
    }

    resized() {
      this.w = p.textWidth(this.button_name) + 14;
      this.h = font_pixels + 10;

      this.x = (report_enabled?w_padding/4:w_padding/2) + this.w / 2 - 7;
      this.y = p.map(this.button_id, 0, 15, h_padding, p.height - h_padding);
      this.text_x = this.x - this.w / 2 + 7;
      this.text_y = this.y - 6;

   
    }

    run() {
      this.update();
      this.display();
    }

    update() {

      if (this.mouseInRegion() && current_survey_topic == 0) {
        this.fillAlpha = 255;
      } else {
        this.fillAlpha = 100;
      }

    }

    display() {


      p.textSize(font_pixels)
      p.textAlign(p.LEFT, p.CENTER)
      p.fill(255, this.fillAlpha);
      p.rect(this.x, this.y, this.w, this.h, 4, 4);
      p.fill(0, 255);
      p.text(this.button_name, this.text_x, this.text_y);
    }


  }


  document.oncontextmenu = function () {
    return false;
  }


}