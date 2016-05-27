//  Chord reader
function chordRdr (matrix, mpr) {
  return function (d) {
  // console.log(d);

    var i, j, sourceNode, targetNode, g;
    var mapper = {};

    if (d.source) {
      i = d.source.index;
      j = d.target.index;
      sourceNode = _.where(mpr, {id: i });
      // console.log(s);
      targetNode = _.where(mpr, {id: j });
      // console.log(t);
      mapper.sourceName = sourceNode[0].name;
      mapper.sourceData = d.source.value;
      mapper.sourceValue = +d.source.value;
      mapper.sourceTotal = _.reduce(matrix[i], function (k, n) { return k + n; }, 0);
      mapper.targetName = targetNode[0].name;
      mapper.targetData = d.target.value;
      mapper.targetValue = +d.target.value;
      mapper.targetTotal = _.reduce(matrix[j], function (k, n) { return k + n; }, 0);
    } else {
      g = _.where(mpr, {id: d.index });
      mapper.gname = g[0].name;
      mapper.gdata = g[0].data;
      mapper.gvalue = d.value;
    }
    mapper.mtotal = _.reduce(matrix, function (m1, n1) {
      return m1 + _.reduce(n1, function (m2, n2) { return m2 + n2; }, 0);
    }, 0);
    return mapper;
  };
}
