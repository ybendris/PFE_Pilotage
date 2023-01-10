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

  chart: any

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


  ngOnInit(): void {
    Chart.register(ChartStreaming)
    this.chart = new Chart("dataChart", {
      type: 'line',
      data: {
        labels: [],
        datasets: []
      },
      options: {
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
    });

    //Abonnement à data$ de chartDataService
    this.chartDataService.data$.subscribe(data => {
    //Certainement à opti plus tard
      console.log(data)

      if(data.expediteur == ''){
        return
      }

      let datasetNumber = this.chart.data.datasets.length

      //On check si il y a déjà une courbe qui correspond à la mesure
      for(let i = 0; i<this.chart.data.datasets.length; i++){
        if(this.chart.data.datasets[i].label == data.paquet){
          datasetNumber = i
        }
      }
      let color = this.getRandomColor()

      //Si il n'y a pas de courbe de la mesure on la rajoute
      if(datasetNumber == this.chart.data.datasets.length){
        this.chart.data.datasets.push({
          label: data.paquet,
          data: [],
          borderColor: color,
          backgroundColor: color
        })
      }

      //MAJ des données de la courbe
      data.msg.forEach( message => {
        console.log("ICI",typeof message.time)
       
        //let timeDate = message.time.replace(/\D/g,'');//Supprime tout ce qui n'est pas un chiffre
        let timeDate = message.time
        console.log(new Date(timeDate))
        this.chart.data.datasets[datasetNumber].data.push({
          x: new Date(timeDate),
          y: message.data
        });
      });
      this.chart.update();//Update du graphique

    });

  }



}
