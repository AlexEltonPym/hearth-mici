
class Effect {
    constructor(label_name,effect_short,methods, param_format, targets, filters, duration) {
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
  