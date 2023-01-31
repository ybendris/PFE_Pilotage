import {ChangeDetectorRef, Component, OnInit, ViewChild} from '@angular/core';
import Chart from "chart.js/auto";
import ChartStreaming from 'chartjs-plugin-streaming';
import {ChartDataService} from "../../services/chart-data.service";
import 'chartjs-adapter-luxon';
import {MatTable, MatTableDataSource} from "@angular/material/table";



@Component({
  selector: 'app-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.scss']
})
export class ChartComponent {

  @ViewChild(MatTable) table: MatTable<any>;

  //Liste des graphiques
  graphs = [{id: 1, chart: null}]

  //Tableau de couleur pour forcer la couleur des courbes
  //colors = ["#36a2eb", "#ff6384", "#4bc0c0", "#ff9f40", "#9966ff", "#ffcd56"]
  //indexColor = 0

  //Nom des colonnes du tableau pour le BAP
  displayedColumns = ['heure_tnp','sabp','dabp','mabp','hr','trigger'];
  //Données du tableau
  dataSource = [];

  //Option pour les graphiques avec temps réel
  option =  {
    responsive: true,
    scales: {
      x: {
        type: 'realtime',
        realtime: {
          duration: 10000, //Duration of the chart in milliseconds (how much time of data it will show)
          delay: 2000 //Delay added to the chart in milliseconds so that upcoming values are known before lines are plotted. This makes the chart look like a continual stream rather than very jumpy on the right hand side. Specify the maximum expected delay.
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value' //TODO unité mesure + multi axis
        },
        max: 3000

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

  constructor(private  chartDataService: ChartDataService, private cdr: ChangeDetectorRef) {
  }


  //Génère une couleur aléatoire
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
    //Ajouter le plugin streaming
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
      //console.log("New Data ", data)

      //Si l'expediteur est le BAP alors affiché les données dans le tableau
      if(data.expediteur == "BAP"){
        //console.log("BAP " + data.msg)
        //console.log(this.dataSource)
        this.dataSource.push(data.msg)
        this.table.renderRows()
        return
      }

      //On choisit les paquets que l'on veut afficher, ici on affiche uniquement le paquet "measure"
      //si on veut afficher tous les paquets remplacer data.paquet != "measure" par !data.paquet.includes("measure")
      if(data.expediteur == '' || data.paquet != "measure"){ //!data.paquet.includes("measure")
        return
      }

      //Boucle sur chaque trame
      Object.keys(data.msg).forEach( message => {
        //boucle sur chaque clé de la trame
        Object.keys(data.msg[message]).forEach(cle => {
          if(cle != "time" && cle!="timestamp") {
            //Récup de l'ID du graphique si la mesure est déjà présente
            let graphId = this.findGraphId(cle)
            //console.log("graphId ", graphId)

            //Si il n'y a pas de courbe de la mesure on la rajoute sur le 1er graph
            if (!graphId) {
              this.graphs[0].chart.data.datasets.push({
                label: cle,
                data: [],
                borderColor: this.getRandomColor(), //this.colors[this.indexColor] //si couleur fixé
              })
              //this.indexColor++ //si couleur fixé
              graphId = 1
            }
            //recup de l'index du graphs correspondant
            let graphIndex = this.graphs.findIndex(graph => graph.id === graphId);
            //console.log("graphIndex ", graphIndex)
            //console.log("this.graphs[graphIndex] ", this.graphs[graphIndex])

            //recup de l'index de la courbe du graphique correspondant
            let datasetIndex = this.graphs[graphIndex].chart.data.datasets.findIndex(dataSet => dataSet.label === cle)

            //On récupére la date de la trame
            let timeDate = data.msg[message]["time"]
            //console.log("timeDate", timeDate)
            //console.log(cle, " : ", data.msg[message][cle])

            //MAJ des données de la courbe
            this.graphs[graphIndex].chart.data.datasets[datasetIndex].data.push({
              x: new Date(timeDate),
              y: data.msg[message][cle]
            })

          }
        })
      });
      this.graphs.forEach(graph => {
        graph.chart.update();//Update de tous les graphiques, une fois toutes les données ajoutées pour éviter le lag
      })
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

  //permet de supprimer un graphique -- Ne fonctionne pas -- bug par la suite lorsque l'on veut ajouter les données de la dernière mesure du graphique supprimé
  removeGraph(graphId: number){
    //recup de l'index à supprimer
    let index = this.graphs.findIndex(graph => graph.id === graphId);
    //console.log("INDEX REMOVE", index)
    //destroy du graphique
    this.graphs[index].chart.destroy()//bug
    //suppression du graphique de la liste graphs
    this.graphs.splice(index, 1);
    //console.log("REMOVE GRAPH", this.graphs)
  }
}
