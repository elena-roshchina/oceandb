<script>Highcharts.chart('container', {
                chart: {
                    type: 'scatter',
    zoomType: 'xy'
  },
  title: {
    text: 'Станции'
  },
  subtitle: {
    text: 'Source: ARGO'
  },
  xAxis: {
    title: {
      enabled: true,
      text: 'km'
    },
    startOnTick: true,
    endOnTick: true,
    showLastLabel: true
  },
  yAxis: {
    title: {
      text: 'km'
    }
  },
  legend: {
    layout: 'vertical',
    align: 'left',
    verticalAlign: 'top',
    x: 100,
    y: 70,
    floating: true,
    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
    borderWidth: 1
  },
  plotOptions: {
    scatter: {
      marker: {
        radius: 5,
        states: {
          hover: {
            enabled: true,
            lineColor: 'rgb(100,100,100)'
          }
        }
      },
      states: {
        hover: {
          marker: {
            enabled: false
          }
        }
      },
      tooltip: {
        headerFormat: '<b>{series.name}</b><br>',
        pointFormat: '{point.x} km, {point.y} km'
      }
    }
  },
  series: [{
    name: 'Станции',
    color: 'rgba(223, 83, 83, .5)',
    data: {{ points }}
  }]
});
