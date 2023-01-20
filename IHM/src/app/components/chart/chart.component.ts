import {Component, OnInit} from '@angular/core';
import Chart from "chart.js/auto";
import ChartStreaming from 'chartjs-plugin-streaming';
import {ChartDataService} from "../../services/chart-data.service";
import 'chartjs-adapter-luxon';



@Component({
  selector: 'app-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.scss']
})
export class ChartComponent {

  graphs = [{id: 1, chart: null}]

  option =  {
    responsive: true,
    scales: {
      x: {
        type: 'realtime',
        realtime: {
          duration: 10000,
          delay: 2000
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value'
        }
      }
    },
    interaction: {
      intersect: false
    },
    animation: false,
    datasets: {
      line: {
        pointRadius: 0 // disable for all `'line'` datasets
      }
    },
    elements: {
      point: {
        radius: 0 // default to disabled in all datasets
      }
    }
  }

  constructor(private  chartDataService: ChartDataService) {
  }

  getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }


  ngAfterViewInit(): void {
    Chart.register(ChartStreaming)
    console.log(`dataChart${1}`)
    console.log(this.graphs)
    this.graphs[0].chart = new Chart('dataChart1', {
      type: 'line',
      data: {
        labels: [],
        datasets: []
      },
      options: this.option
    });

    //Abonnement à data$ de chartDataService
    this.chartDataService.data$.subscribe(data => {
    //Certainement à opti plus tard
      console.log(data)

      if(data.expediteur == ''){
        return
      }

      let graphId = this.findGraphId(data.paquet)
      console.log(graphId)

      //Si il n'y a pas de courbe de la mesure on la rajoute sur le 1er graph
      if(!graphId){
        this.graphs[0].chart.data.datasets.push({
          label: data.paquet,
          data: [],
          borderColor: this.getRandomColor(),
        })
        graphId = 1
      }
      //recup de l'index du graphs correspondant
      let graphIndex = this.graphs.findIndex(graph => graph.id === graphId);
      console.log(graphIndex)
      console.log(this.graphs[graphIndex])

      let datasetIndex = this.graphs[graphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === data.paquet)

      //MAJ des données de la courbe
      data.msg.forEach( message => {
        console.log("ICI",typeof message.time)

        //let timeDate = message.time.replace(/\D/g,'');//Supprime tout ce qui n'est pas un chiffre
        let timeDate = message.time
        console.log(new Date(timeDate))
        console.log(datasetIndex)
        this.graphs[graphIndex].chart.data.datasets[datasetIndex].data.push({
          x: new Date(timeDate),
          y: message.data
        });
      });
      this.graphs[graphIndex].chart.update();//Update du graphique

    });

  }
  //TODO modif graphs[0].chart par le graph d'origine de la courbe
  createNewGraphWithDataset(label: string) {
    let data = {
      labels: [],
      datasets: []
    };
    let graphId = this.findGraphId(label)
    //recup de l'index du graphs correspondant
    let graphIndex = this.graphs.findIndex(graph => graph.id === graphId);

    let datasetIndex = this.graphs[graphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === label)
    let dataset = this.graphs[graphIndex].chart.data.datasets.splice(datasetIndex,1)

    if (dataset.length > 0) {
      let nextId = this.graphs[this.graphs.length - 1].id + 1
      data.datasets.push(dataset[0]);
      // Create new chart with filtered data
      var canvas = document.createElement('canvas');
      canvas.id = `dataChart${nextId}`;
      document.getElementById('graphsId').appendChild(canvas);
      var ctx = canvas.getContext('2d');
      var newChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: this.option
      });
      console.log("nextId: ", nextId)
      this.graphs.push({id: nextId, chart: newChart});
    }
  }

  findGraphId(label: string) {
    let graphId;
    this.graphs.forEach((graph) => {
      graph.chart.data.datasets.forEach((dataset) => {
        if (dataset.label === label) {
          graphId = graph.id;
        }
      });
    });
    return graphId
  }

  changeGraphData(label :string, toGraphId: number){
    let fromGraphId = this.findGraphId(label)
    let fromGraphIndex = this.graphs.findIndex(graph => graph.id === fromGraphId);
    let toGraphIndex = this.graphs.findIndex(graph => graph.id === toGraphId);

    let datasetIndex = this.graphs[fromGraphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === label)
    let dataset = this.graphs[fromGraphIndex].chart.data.datasets.splice(datasetIndex,1)

    if (dataset.length > 0) {
      let nextId = this.graphs[this.graphs.length - 1].id + 1
      this.graphs[toGraphIndex].chart.data.datasets.push(dataset[0])
    }
  }


  /*
  TODO Multiple graph:
    - Switch données d'un graph à l'autre V
    - mat-grid html evolutif
    - Supp graph quand plus de données
   */




}
