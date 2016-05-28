// creates toggle button
function toggle(source) {
          checkboxes = document.getElementsByName('calendar');
          for(var i=0, n=checkboxes.length;i<n;i++) {
            console.log(checkboxes[i]);
            checkboxes[i].checked = source.checked;
          }
          sendSelected();
        }

// sends checkbox data to server, receives json to render chord diagram
function sendSelected() {

  var selectedCals = $("#selected-calendars input").serializeArray();

  $.get("/chord_diagram.json", selectedCals,
          function(data) {
          var mpr = data['mpr'];
          var meetingsMatrix = data['meetingsMatrix'];
          drawChords(meetingsMatrix, mpr);
          }
  );
}

// draws chord diagram
function drawChords (matrix, mpr) {
  var w = 720, h = 540, r1 = h / 2, r0 = r1 - 110;

  $(".diagram").empty();

  // sets color palette 
  // var fill = d3.scale.category20b()
  var fill = d3.scale.ordinal()
      .range(['#d4d7d9','#3c3c3c','#bd7aa9','#848589','#884e7a',
              '#6a657c','#606165','#9999a4','#61475d','#8ca49c',]);

  // constructs a new chord layout
  var chord = d3.layout.chord()
      .padding(.02)
      .sortSubgroups(d3.descending)
      .sortChords(d3.descending);

  // radius of inner and outer arcs
  var arc = d3.svg.arc()
      .innerRadius(r0 + 15)
      .outerRadius(r0 + 7);

  // TODO: { 'megan:ryan': ['event 1', 'event 2']}


  var svg = d3.select(".diagram").append("svg:svg")
      .attr("viewBox","0 0 780 600")
      .attr("preserveAspectRatio","xMidYMid meet")  // makes diagram responsive
      .append("svg:g")
      .attr("id", "circle")
      // centering on half width, half height
      .attr("transform", "translate(" + (w / 2) + "," + (h / 2) + ")");
      svg.append("circle")
          .attr("r", r0 + 20);

  var rdr = chordRdr(matrix, mpr);
  chord.matrix(matrix);

  // mousover and mouseout for tooltip
  var g = svg.selectAll("g.group")
      .data(chord.groups())
      .enter().append("svg:g")
      .attr("class", "group")
      .on("mouseover", mouseover)
      .on("mouseout", function (d) { d3.select("#tooltip").style("visibility", "hidden");} );

  g.append("svg:path")
      // border color for nodes
      .style("stroke", "black")
      .style("fill", function(d) { return fill(rdr(d).hoverName); })
      .attr("d", arc);

  // node labels
  g.append("svg:text")
      .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
      .attr("dy", ".35em")
      .style("font-family", "helvetica, arial, sans-serif")
      .style("font-size", "11px")
      .attr("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })

  // rotates node labels
  .attr("transform", function(d) {
    return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
      + "translate(" + (r0 + 26) + ")"
      + (d.angle > Math.PI ? "rotate(180)" : "");
  })
    .text(function(d) { return rdr(d).hoverName; });

    var chordPaths = svg.selectAll("path.chord")
      .data(chord.chords())
      .enter().append("svg:path")
      .attr("class", "chord")
      .style("stroke", function(d) { return d3.rgb(fill(rdr(d).sourceName)).darker(); })
      .style("fill", function(d) { return fill(rdr(d).sourceName); })
      .attr("d", d3.svg.chord().radius(r0))
      .on("mouseover", function (d) {
          d3.select("#tooltip")
          .style("visibility", "visible")
          .html(chordTip(rdr(d)))  // calls chord tip
          .style("top", function () { return (d3.event.pageY - 170)+"px";})  // sets location of hover text
          .style("left", function () { return (d3.event.pageX - 100)+"px";});
          })
          .on("mouseout", function (d) { d3.select("#tooltip").style("visibility", "hidden");});

          // hover text
          function chordTip (d) {
            moment.relativeTimeThreshold('s', 60);
            moment.relativeTimeThreshold('m', 60);
            moment.relativeTimeThreshold('h', 24);
            moment.relativeTimeThreshold('d', 30);
            moment.relativeTimeThreshold('M', 12);
            var p = d3.format(".1%");
            return ""
              +  d.sourceName + "'s time with " + d.targetName + ": "
                + (moment.duration((d.sourceValue), "minutes").humanize()) + "<br>"
              + p(d.sourceValue/d.sourceTotal) + " of " + d.sourceName + "'s time <br>"
              + p(d.sourceValue/d.mtotal) + " of team total" + "<br>"
              + "<br>"
              + d.targetName + "'s time with " + d.sourceName + ": " 
                + (moment.duration((d.targetValue), "minutes").humanize()) + "<br>"
              + p(d.targetValue/d.targetTotal) + " of " + d.tname + "'s time <br>"
              + p(d.targetValue/d.mtotal) + " of team total";

          }

  function groupTip (d) {
    var p = d3.format(".1%");
    return "" + d.hoverName + ": " + p(d.hoverValue/d.mtotal) + " of team total";

  }

  function mouseover(d, i) {
    d3.select("#tooltip")
      .style("visibility", "visible")
      .html(groupTip(rdr(d)))
      .style("top", function () { return (d3.event.pageY - 80)+"px";})
      .style("left", function () { return (d3.event.pageX - 130)+"px";});

    chordPaths.classed("fade", function(p) {
      return p.source.index != i && p.target.index != i;
    });
  }

  //  Chord reader
  function chordRdr (matrix, mpr) {
    return function (d) {

      var i, j, sourceNode, targetNode, hoverNode;
      var mapper = {};

      if (d.source) {
        i = d.source.index;
        console.log(i);
        j = d.target.index;
        sourceNode = _.where(mpr, {id: i });
        targetNode = _.where(mpr, {id: j });
        mapper.sourceName = sourceNode[0].name;
        mapper.sourceData = d.source.value;
        mapper.sourceValue = +d.source.value;
        mapper.sourceTotal = _.reduce(matrix[i], function (k, n) { return k + n; }, 0);
        mapper.targetName = targetNode[0].name;
        mapper.targetData = d.target.value;
        mapper.targetValue = +d.target.value;
        mapper.targetTotal = _.reduce(matrix[j], function (k, n) { return k + n; }, 0);
      } else {
        hoverNode = _.where(mpr, {id: d.index });
        mapper.hoverName = hoverNode[0].name;
        mapper.hoverData = hoverNode[0].data;
        mapper.hoverValue = d.value;
      }
      mapper.mtotal = _.reduce(matrix, function (m1, n1) {
        return m1 + _.reduce(n1, function (m2, n2) { return m2 + n2; }, 0);
      }, 0);
      return mapper;
    };
  }
}