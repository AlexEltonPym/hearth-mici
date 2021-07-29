

export default function Button(p){

    p.constructor = (button_name, button_id) => {
      this.button_name = button_name;
      this.button_id = button_id;
  
      this.x = 0;
      this.y = 0;
      this.w = textWidth(button_name) + 14;
      this.h = font_pixels + 10;
      this.fillAlpha = 100;

      this.text_x = 0;
      this.text_y = 0;
    }
    p.mouseInRegion = () => {
      return (p.mouseX > this.x - this.w / 2 - mouse_padding &&
        p.mouseX < this.x + this.w / 2 + mouse_padding &&
        p.mouseY > this.y - this.h / 2 - mouse_padding &&
        p.mouseY < this.y + this.h / 2 + mouse_padding);
    }
  
    p.resized = () => {
      this.x = w_padding - 150 + this.w / 2 - 7;
      this.y = p.map(this.button_id, 0, buttons.length, h_padding, height - h_padding);
      this.text_x = this.x - this.w / 2 + 7;
      this.text_y = this.y - 6;
    }
  
    p.run = () => {
      this.update();
      this.display();
    }
  
    p.update = () => {
  
      if (this.mouseInRegion() && current_survey_topic == 0) {
        this.fillAlpha = 255;
      } else {
        this.fillAlpha = 100;
      }
  
    }
  
    p.display = () => {
  
  
      p.textSize(font_pixels)
      p.textAlign(p.LEFT, p.CENTER)
      p.fill(255, this.fillAlpha);
      p.rect(this.x, this.y, this.w, this.h, 4, 4);
      p.fill(0, 255);
      p.text(this.button_name, this.text_x, this.text_y);
    }
  
    
  }