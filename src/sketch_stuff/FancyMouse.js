
export default function FancyMouse(p){
  p.constuctor = () => {
    this.busy = false;
    this.xOffset = 0;
    this.yOffset = 0;
    this.effect = null;
  }
  p.setOffset = (buttonX, buttonY) => {
    this.xOffset = p.mouseX - buttonX;
    this.yOffset = p.mouseY - buttonY;
  }
}