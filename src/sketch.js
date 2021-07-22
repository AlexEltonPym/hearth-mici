export default function sketch(p){
    let canvas;



    p.setup = () => {
        canvas = p.createCanvas(p.windowWidth, 300)
    }

    p.draw = () => {
        p.background(255, 100, 100);
    }

}