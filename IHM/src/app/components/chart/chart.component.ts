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
          text: 'Value' //TODO unité mesure + multi axis
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

//Aprés chargement de l'HTML
  ngAfterViewInit(): void {
    Chart.register(ChartStreaming)
    //console.log(`dataChart${1}`)
    //console.log(this.graphs)

    //Création du graph de base
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
      console.log("New Data ", data)

      if(data.expediteur == ''){
        return
      }
      //Récup de l'ID du graphique si la mesure est déjà présente
      let graphId = this.findGraphId(data.paquet)
      console.log("graphId ", graphId)

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
      console.log("graphIndex ", graphIndex)
      console.log("this.graphs[graphIndex] ",this.graphs[graphIndex])

      //recup de l'index de la courbe du graphique correspondant
      let datasetIndex = this.graphs[graphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === data.paquet)

      //MAJ des données de la courbe
      data.msg.forEach( message => {
        //console.log("TIME ",typeof message.time)

        //let timeDate = message.time.replace(/\D/g,'');//Supprime tout ce qui n'est pas un chiffre
        let timeDate = message.time
        console.log("DATA", new Date(timeDate), message.data)
        console.log("datasetIndex ", datasetIndex)
        console.log("Datasets ", this.graphs[graphIndex].chart.data.datasets)
        this.graphs[graphIndex].chart.data.datasets[datasetIndex].data.push({
          x: new Date(timeDate),
          y: message.data
        });
      });
      this.graphs[graphIndex].chart.update();//Update du graphique
    });

  }

  //Crée un nouveau graphique avec les données du label passé en paramétre
  createNewGraphWithDataset(label: string) {
    let data = {
      labels: [],
      datasets: []
    };
    //recup l'id du graphique d'origine
    let graphId = this.findGraphId(label)
    //recup de l'index du graphs d'origine
    let graphIndex = this.graphs.findIndex(graph => graph.id === graphId);

    //recup l'index des données
    let datasetIndex = this.graphs[graphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === label)
    //recup des données et suppression des données du graphique d'origine
    let dataset = this.graphs[graphIndex].chart.data.datasets.splice(datasetIndex,1)

    if (dataset.length > 0) {
      //on défini l'ID du nouveau graphique
      let nextId = this.graphs[this.graphs.length - 1].id + 1
      data.datasets.push(dataset[0]);
      // on crée le canvas HTML du nouveau graphique et on ajoute les données
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
      //on ajoute le nouveau graphique dans la liste des graphs
      this.graphs.push({id: nextId, chart: newChart});
    }
  }

  //retourne l'ID du graphique qui contient les données du label en paramètre
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

  //permet d'afficher les données d'un graphqiue à un autre
  changeGraphData(label :string, toGraphId: number){
    //recup de l'ID et de l'index du graph d'origine
    let fromGraphId = this.findGraphId(label)
    let fromGraphIndex = this.graphs.findIndex(graph => graph.id === fromGraphId);
    //recup l'index du graphique de destination
    let toGraphIndex = this.graphs.findIndex(graph => graph.id === toGraphId);

    //recup l'index des données
    let datasetIndex = this.graphs[fromGraphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === label)
    //recup des données et suppréssion des données du graphqiue d'origine
    let dataset = this.graphs[fromGraphIndex].chart.data.datasets.splice(datasetIndex,1)

    if (dataset.length > 0) {
      //ajout des données dans le graphique de destination
      this.graphs[toGraphIndex].chart.data.datasets.push(dataset[0])
    }
    //si le graphique d'origine n'a plus de données alors on le supprime
    if(fromGraphId !=0 && this.graphs[fromGraphIndex].chart.data.datasets.length == 0){
      console.log("remove graph")
      //this.removeGraph(fromGraphId)
    }
  }

  //permet de supprimer un graphique -- Ne fonctionne pas
  removeGraph(graphId: number){

    let index = this.graphs.findIndex(graph => graph.id === graphId);
    console.log("INDEX REMOVE", index)
    this.graphs[index].chart.destroy()//bug
    this.graphs.splice(index, 1);
    console.log("REMOVE GRAPH", this.graphs)
  }
}
