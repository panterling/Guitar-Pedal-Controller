import 'package:dart_app/Pedal/PedalBloc.dart';
import 'package:dart_app/Widgets/PedalNumericControlWidget.dart';
import 'package:dart_app/Widgets/ReverbPanelBlocWidget.dart';
import 'package:dart_app/Widgets/ReverbPanelWidget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';


class ConnectedWidget extends StatelessWidget{
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Container(
                margin: const EdgeInsets.all(2.0),
                padding: const EdgeInsets.all(8.0),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(3.0),
                ),
                child: Row(
                  children: [
                    Text(
                      "U-- CURRENT PATCH",
                      style: TextStyle(fontWeight: FontWeight.bold, fontFamily: "monospace"),
                    )
                  ],
                  mainAxisAlignment: MainAxisAlignment.center,
                ),
              )
            ],
          ),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            //Container(margin: const EdgeInsets.fromLTRB(3, 1, 3, 1), child: RaisedButton(child: Text("?"), color: Colors.lightBlueAccent, onPressed: (){},)),
            Container(
                margin: const EdgeInsets.fromLTRB(3, 1, 3, 1),
                child: RaisedButton(
                  child: Text("Tuner"),
                  color: Colors.lightBlueAccent,
                  onPressed: () {},
                )),
            //Container(margin: const EdgeInsets.fromLTRB(3, 1, 3, 1), child: RaisedButton(child: Text("?"), color: Colors.lightBlueAccent, onPressed: (){},)),
          ]),
          Expanded(
              child: DefaultTabController(
                length: 6,
                child: Scaffold(
                  appBar: new PreferredSize(
                    preferredSize: Size.fromHeight(kToolbarHeight),
                    child: new Container(
                        color: Colors.blue,
                        child: new SafeArea(
                            child: Column(children: <Widget>[
                              new Expanded(child: new Container()),
                              new TabBar(
                                tabs: [
                                  Tab(text: "FX1"),
                                  Tab(text: "OD"),
                                  Tab(text: "Pr"),
                                  Tab(text: "FX2"),
                                  Tab(text: "De"),
                                  Tab(text: "Re"),
                                ],
                              )
                            ]))),
                  ),
                  body: TabBarView(
                    children: [
                      Icon(Icons.directions_car),
                      Icon(Icons.directions_transit),
                      Icon(Icons.directions_bike),
                      Icon(Icons.directions_run),
                      Icon(Icons.error),
                      ReverbPanelBlocWidget(),
                    ],
                  ),
                ),
              ))
        ],
      ),
    );
  }
}
