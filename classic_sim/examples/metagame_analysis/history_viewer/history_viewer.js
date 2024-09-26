// dataset = []

// d3.csv("example_history.csv", (data) => {
//   dataset.push(data)
//   if (dataset.length == 100) {
//     dataset_loaded(dataset)
//   }
// });


// function dataset_loaded(dataset) {
//   for (let generation of dataset) {
//     let i = 0
//     let generation_clusters = []
//     for (let entry in generation) {
//       if (i % 4 == 3) {
//         generation_clusters.push(generation[entry])
//       }
//       i++
//     }

//   }

//   draw_plot(null)
// }

  var color = d3.scaleOrdinal(d3.schemeCategory10);

 // Data
 var graph = {
   nodes: [
     {"id": "n", "title": "Second Source", "color": color("n")},
     {"id": "a", "title": "Source", "color": color("x")},
     {"id": "b", "title": "Stage 1","color": color("y")},
     {"id": "c", "title": "Stage 2", "color": color("z")},
     {"id": "d", "title": "Output\nflow", "color": color("1")},
     {"id": "e", "title": "Losses", "color": color("2")},
   ],
   links: [
    {"source": "n", "target": "b", "type": "x", "values": 2},
     {"source": "a", "target": "b", "type": "x", "values": 2},
     {"source": "b", "target": "c", "type": "x", "values": 1.5},
     {"source": "a", "target": "c", "type": "y", "values": 1},
     {"source": "a", "target": "c", "type": "z", "values": 2},
     {"source": "c", "target": "d", "type": "0", "values": 3},
     {"source": "b", "target": "e", "type": "1", "values": 0.5},
     {"source": "c", "target": "e", "type": "1", "values": 1.5},
     {"source": "a", "target": "e", "type": "1", "values": 0.5}
   ]
 };

 let order = [
  ["a", "n", "b"],
  ["c", "d", "e"]
 ]

 // Set up SVG
 var svg = d3.select('svg');
 var width = +svg.attr('width');
 var height = +svg.attr('height');
 var margin = { top: 10, left: 100, bottom: 10, right: 50 };

 var layout = d3.sankey()
                .linkValue(function (d) { return d.values; })
                .nodeWidth(30)
                .ordering(order)
                .extent([
                  [margin.left, margin.top],
                  [width - margin.left - margin.right, height - margin.top - margin.bottom]]);

 // Render
 var fmt = d3.format('.1f');
 var diagram = d3.sankeyDiagram()
                 .linkMinWidth(function(d) { return 0.1; })
                 .nodeValue(nodeValue)
                 .linkColor(function(d) { return color(d.type); })


 update();

 function update() {
   layout(graph);

   svg
     .datum(graph)
     .call(diagram);
 }

 

 function nodeValue(d) {
   return fmt(d.value);
 }

  