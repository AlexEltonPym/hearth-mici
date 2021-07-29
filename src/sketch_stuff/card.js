
class Card {
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

    resized() {
        this.x = map(this.card_id + 1, 0, cards.length, w_padding, width - w_padding)
        this.y = height / 2;
    }

    run() {
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

    display() {
        push();
        fill(0);
        textAlign(CENTER, CENTER)
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
            image(flav, this.x + 5, this.y - 50, 300, 300)
        }
        image(forg, this.x, this.y, this.w, this.h);

        push();
        textSize(60);
        fill(255);
        strokeWeight(3);
        stroke(0);

        if (card_types[this.type_id] == "minion") {
            text(this.power, this.x-this.w/2.99, this.y+this.h/2.8)
            text(this.toughness, this.x+this.w/2.6, this.y+this.h/2.8)
        }

      
        text(this.mana, this.x-this.w/2.99, this.y-this.h/2.3)
       
        pop();

       
        push();
        fill(0);
        textSize(smaller_font_size);
        let translation_offset_y;
        if(this.oversized){
            translation_offset_y = this.y - this.h/2 + 80;
            translate(this.x, this.y - this.h/2 + 80);
        } else {
            translation_offset_y = this.y  + 50;
            translate(this.x, this.y + 50);
        }
        
        this.mouse_over_card_effect = false;
        this.hovered_effect = null;
        for(let e of this.effects){
            
            translation_offset_y += e.effect_string_height/2;
            translate(0, e.effect_string_height/2)

            if(mouseY > translation_offset_y - e.effect_string_height/2 &&
                mouseY < translation_offset_y + e.effect_string_height/2 &&
                mouseX > this.x - e.effect_string_width/2 &&
                mouseX < this.x + e.effect_string_width/2){

                this.mouse_over_card_effect = true;

                this.hovered_effect = e;
                this.hovered_effect.x = this.x - e.effect_string_width/2;
                this.hovered_effect.y = translation_offset_y - e.effect_string_height;
                fill(0, 100);
            } else {
                fill(0, 50)
            }

            rect(0, 0, e.effect_string_width, e.effect_string_height, 4, 4)
            fill(255, 255)
            text(e.effect_string, 0, 0, blank_spell_img.width/2, blank_spell_img.height/2)
            translation_offset_y += e.effect_string_height/2+5;
            translate(0, e.effect_string_height/2+5)

        }
        pop();


        push();

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

        pop();
    }


    mouseInImg() {
        return (mouseX > this.x - this.w / 2 - mouse_padding &&
            mouseX < this.x + this.w / 2 + mouse_padding &&
            mouseY > this.y - this.h / 2 - mouse_padding &&
            mouseY < this.y + this.h / 2 + mouse_padding);

    }
    check_mouse_hovers() {
        if (card_types[this.type_id] == "minion") {
            this.mouse_over_power = dist(mouseX, mouseY, this.x-this.w/2.99, this.y+this.h/2.8) < 50
            this.mouse_over_toughness = dist(mouseX, mouseY, this.x+this.w/2.6, this.y+this.h/2.8) < 50
        }
        this.mouse_over_mana = dist(mouseX, mouseY, this.x-this.w/2.99, this.y-this.h/2.3) < 50
    }


}
