import { Component } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  sessionName = ''
  sessionDescription = ''

  constructor(private router: Router, private activatedRoute: ActivatedRoute) {
    console.log(this.router.getCurrentNavigation().extras.state)
    this.sessionName = this.router.getCurrentNavigation().extras.state["name"]
    this.sessionDescription = this.router.getCurrentNavigation().extras.state["description"]
  }

}
