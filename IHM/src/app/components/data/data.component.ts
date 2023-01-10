import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {SocketService} from "../../services/socket.service";
import {ChartDataService} from "../../services/chart-data.service";

@Component({
  selector: 'app-data',
  templateUrl: './data.component.html',
  styleUrls: ['./data.component.scss']
})
export class DataComponent implements OnInit {

  constructor(public socketService: SocketService, private chartDataService: ChartDataService) { }

  ngOnInit(): void {
    /*
    Le composant s'abonne aux deux fonctions de socketService afin de récupérer et de traiter les données reçus
     */

    this.socketService.getData().subscribe(data => {
      console.log("Data reçus :" + data)
      this.chartDataService.updateData(data)
    })

    this.socketService.getLog().subscribe(log => {
      console.log("Log reçus :" + JSON.stringify(log))
    })
  }


}
