$(".diagram").html("<p>Choose calendars</p>");

// settings for date picker
$(function() {
    $( ".datepicker" ).datepicker();
    $( "#startdate" ).datepicker( "setDate", "+0d" );
    $( "#enddate" ).datepicker( "setDate", "+2w" );
});

// creates select all button
function selectAll(source) {
    checkboxes = document.getElementsByName('calendar');
    for(var i=0, n=checkboxes.length;i<n;i++) {
      checkboxes[i].checked = source.checked;
    }
    if ($('.select-all.active')[0]) {
      $('.selectable').addClass('active');
    } else {
      $('.selectable').removeClass('active');
    }
    sendFilters();
  }

// on change event for drop down date picker
$( ".datepicker" ).change(
  function () { sendFilters(); }
);

// on change event for calendar buttons
$( 'input[name="radio-chart"]' ).change(
  function () { sendFilters(); }
);

// sends checkbox data to server, receives json to render chord diagram
function sendFilters() {
  var filters = getFilters();

  $.get("/chord-diagram.json", filters,
          function(data) {
          var mpr = data['mpr'];
          var meetingsMatrix = data['meetingsMatrix'];
          var emptyMatrix = data['emptyMatrix'];
          buildCharts(meetingsMatrix, emptyMatrix, mpr, filters);
          }
  );
}

// returns object with selected calendars and dates
function getFilters() {
  var filters = $("#selected-calendars input").serializeArray();
  console.log(filters);
  var startdate = $("#startdate").val();
  var enddate = $("#enddate").val();

  filters.push({name: "startdate", value: startdate});
  filters.push({name: "enddate", value: enddate});

  return filters;
}

// builds chart or provides message
function buildCharts (meetingsMatrix, emptyMatrix, mpr, filters) {
  var chartType = $('input[name="radio-chart"]:checked').val();
  var selectedCals = filters.slice(0,-2).length;

  if (selectedCals == 0) {
    zeroCalendars(chartType);
  } else if (selectedCals == 1) {
    oneCalendar(chartType);
  } else if (selectedCals > 1) {
    multipleCalendars(chartType, meetingsMatrix, emptyMatrix, mpr);
  }
}

function zeroCalendars(chartType) {
    if (chartType == "chord") {
      $(".diagram").empty();
      $(".diagram").html("<p>Choose calendars</p>");
    } else {
      $(".diagram").empty();
      $(".diagram").html("<p>Choose one calendar</p>");
    }
}

function oneCalendar(chartType) {
  if (chartType == "doughnut") {
        sendDoughnutData();
  } else if (chartType == "chord") {
        $(".diagram").empty();
        $(".diagram").html("<p>Choose additional calendars</p>");
  }
}

function multipleCalendars(chartType, meetingsMatrix, emptyMatrix, mpr) {
  if (chartType == "chord") {
    if (_.isEqual(meetingsMatrix, emptyMatrix)) {
      $(".diagram").empty();
      $(".diagram").html("<p>No meetings between these calendars</p>");
    } else {
      drawChords(meetingsMatrix, mpr);
  }} else if (chartType == "doughnut") {
    $(".diagram").empty();
    $(".diagram").html("<p>Choose one calendar</p>");
  }
}

// doughnut chart
function sendDoughnutData() {
  var filters = getFilters();
  
  $.get("/doughnut.json", filters, function(response) {
    buildDoughnut(response);
  });
}

function buildDoughnut(response) {
  var durations = response['durations'];
  var labels = response['labels'];
  $(".diagram").empty();
  $(".diagram").html('<canvas id="myChart" width="550" height="500"></canvas>');
  var selectedName = $(".active input").val();
  $('.diagram').prepend('<h4 class="name">'+ selectedName + '\'s<br>meetings</h4>');

  doughnutSettings(durations, labels);
}

function doughnutSettings(durations, labels) {
   var myChart = new Chart(document.getElementById("myChart"), {
    title: {text: "Types of meetings"},
    type: 'doughnut',
    data: {datasets: [{data: durations,
                       backgroundColor: ['#5C6BC0', '#42A3EB', '#eb8a42',
                       '#89544b', '#c0b15c', '#355959', '#4b8089', '#707070'],
                       hoverBackgroundColor: ['#5C6BC0', '#42A3EB', '#eb8a42',
                       '#89544b', '#c0b15c', '#355959', '#4b8089', '#707070']}],
          labels: labels},
    options: {responsive: false,
              elements: {arc: {borderColor: "#fff"}},
              tooltips: {enabled: true,
                         backgroundColor: 'black',
                         yPadding: 10,
                         caretSize: 5}}
  });
}

/////////////////////////////////////////////////////////////////////
// d3 chord diagram based on examples from http://www.delimited.io //
/////////////////////////////////////////////////////////////////////


// draws chord diagram
function drawChords (matrix, mpr) {
  var w = 750, h = 700, r1 = h / 2, r0 = r1 - 110;

  $(".diagram").empty();
  $(".diagram").empty();

  var fill = d3.scale.ordinal()
      .range([ '#707070', '#4b8089', '#c0b15c', '#eb8a42', '#5C6BC0', '#42A3EB',
               '#89544b', '#355959']);

  // constructs a new chord layout
  var chord = d3.layout.chord()
      .padding(.02)
      .sortSubgroups(d3.descending)
      .sortChords(d3.descending);

  // radius of inner and outer arcs
  var arc = d3.svg.arc()
      .innerRadius(r0 + 15)
      .outerRadius(r0 + 7);

  var svg = d3.select(".diagram").append("svg:svg")
      .attr("width", w)
      .attr("height", h)
      // .attr("viewBox","0 0 650 600") // makes diagram responsive
      // .attr("preserveAspectRatio","xMidYMid meet")  
      .append("svg:g")
      .attr("id", "circle")
      // centering d3 diagram in svg
      .attr("transform", "translate(" + (350) + "," + (h / 2) + ")");
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
      .style("font-size","150px")
      .style("fill", function(d) { return fill(rdr(d).hoverName); })
      .attr("d", arc);

  // node labels
  g.append("svg:text")
      .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
      .attr("dy", ".35em")
      .style("font-family", "Roboto, sans-serif")
      .style("font-size", "15px")
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

          // tooltip hover text
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
              + p(d.targetValue/d.targetTotal) + " of " + d.targetName + "'s time <br>"
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
      .style("left", function () { return (d3.event.pageX - 200)+"px";});

    chordPaths.classed("fade", function(p) {
      return p.source.index != i && p.target.index != i;
    });
  }

  // Chord reader
  function chordRdr (matrix, mpr) {
    return function (d) {

      var i, j, sourceNode, targetNode, hoverNode;
      var mapper = {};

      if (d.source) {
        i = d.source.index;
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