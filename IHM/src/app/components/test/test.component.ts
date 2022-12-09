import {Component, OnDestroy, OnInit} from '@angular/core';
import {SocketService} from "../../services/socket.service";

@Component({
  selector: 'app-test',
  templateUrl: './test.component.html',
  styleUrls: ['./test.component.scss']
})
export class TestComponent implements OnInit {

  constructor(public socketService: SocketService) { }

  ngOnInit(): void {
    this.socketService.getData().subscribe(data => {
      console.log("Data reçus :" + JSON.stringify(data))
    })

    this.socketService.getLog().subscribe(log => {
      console.log("Log reçus :" + JSON.stringify(log))
    })
  }


}
