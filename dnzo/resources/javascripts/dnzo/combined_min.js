DNZO=Object.extend(DNZO,{load:function(B){var A=$("switcher");if(A){A.observe("change",DNZO.onSwitchList)}$$("a.dialog").each(function(C){new ModalDialog.Ajax(C)});DNZO.verifyTimezone()},strcmp:function(B,A){B=B.toLowerCase();A=A.toLowerCase();if(B==A){return 0}return B<A?-1:1},onSwitchList:function(A){document.location.href=$F(A.element())},verifyTimezone:function(){if(DNZO.timezoneInfo.updateUrl.length==0){return}var A=(new Date()).getTimezoneOffset();if(DNZO.timezoneInfo.offset!=A){new Ajax.Request(DNZO.timezoneInfo.updateUrl,{parameters:{offset:A},method:"post"})}}});Event.observe(window,"load",DNZO.load);var InstantAutocompleter=Class.create({initialize:function(C,A,B){var D={firstSelected:false,continueTabOnSelect:true,tokenSplitter:/[,;]\s*/,beforeMatch:/(?:^|\s)/,transformSeparator:null,multivalue:false};this.options=Object.extend(D,(typeof B!="undefined")?B:{});this.element=C;this.collectionOrCallback=A;this.setupElements();this.wireEvents();this.reset()},setupElements:function(){this.updateElementContainer=new Element("div");this.updateElementContainer.hide();this.updateElement=new Element("ul",{className:"autocompleter"});this.updateElementContainer.appendChild(this.updateElement);this.element.parentNode.appendChild(this.updateElementContainer);this.updateElementContainer.setStyle({position:"absolute",zIndex:2})},wireEvents:function(){this.element.observe("focus",this.onFocus.bind(this));this.element.observe("keydown",this.onKeyDown.bind(this));this.element.observe("keypress",this.onKeyPress.bind(this));this.element.observe("keyup",this.onKeyUp.bind(this));this.updateElementContainer.observe("click",this.onClick.bind(this));this.updateElementContainer.observe("mouseover",this.onHover.bind(this))},reset:function(A){this.hide();this.selectedIndex=-1;this.value=null;this.dontReappear=false;this.matches=[]},onFocus:function(A){this.reset()},onKeyDown:function(B){this.wasShown=this.isShown();var A=false;switch(B.keyCode){case Event.KEY_TAB:if(this.selectEntry()){this.dontReappear=true;A=!this.options.continueTabOnSelect}break;case Event.KEY_RETURN:if(this.selectEntry()){this.dontReappear=true;A=true}break;case Event.KEY_ESC:this.reset();this.dontReappear=true;A=this.wasShown;break;case Event.KEY_LEFT:case Event.KEY_RIGHT:break;case Event.KEY_UP:this.markPrevious();A=true;break;case Event.KEY_DOWN:this.markNext();A=true;break}this.wasStopped=A;if(A){B.stop()}},onKeyPress:function(A){if(this.wasStopped){A.stop()}var B=A.charCode>0&&String.fromCharCode(A.charCode);if(!B){return}if(this.options.multivalue&&B.match(this.options.tokenSplitter)){if(this.selectEntry()){A.stop()}}},onKeyUp:function(A){var B=this.valueChanged();if(this.value.blank()){this.reset()}else{if(this.wasShown){A.stop()}if(B&&!this.dontReappear){this.updateOptions()}}},onHover:function(C){var A=C.element();A=A.match("li")?A:A.up("li");if(!A){return}var B=A.autocompleteIndex;if(B!=null&&this.selectedIndex!=B){this.selectedIndex=B;this.updateSelected()}},onClick:function(A){this.selectEntry();this.dontReappear=true;A.stop();this.element.focus()},isShown:function(){return this.updateElementContainer.visible()},show:function(){this.updateElementContainer.clonePosition(this.element,{setHeight:false,offsetTop:this.element.offsetHeight});this.updateElementContainer.show()},hide:function(){this.updateElementContainer.hide()},valueChanged:function(){var A=this.value;var B=this.getTokens().last();this.value=B;return this.value!=A},updateOptions:function(){var A=this.getSelectedValue();this.updateElement.innerHTML="";this.matches=this.getMatches();if(this.matches.length==0){this.hide();return}this.selectedIndex=this.options.firstSelected?0:-1;this.matches.each(function(D,C){var B=new Element("li");B.autocompleteIndex=C;B.innerHTML=D.escapeHTML();this.updateElement.appendChild(B);if(D==A){this.selectedIndex=C}},this);this.updateSelected();if(!this.isShown()){this.show()}},getCollection:function(){var A=this.collectionOrCallback;if(A instanceof Function){A=A(this.value)}return A},getSelectedValue:function(){return this.matches[this.selectedIndex]},getSelectedElement:function(){return this.updateElement.select("li")[this.selectedIndex]},updateSelected:function(){var B=this.updateElement.select("li");B.each(function(C,D){C.removeClassName("selected")});var A=this.getSelectedElement();if(A){A.addClassName("selected")}},getMatches:function(){var A=this.getRegex();var B=this.getCollection().collect(function(C){if(C.match(A)){return C}return null}).reject(function(C){return !C});if(B.length==1&&B[0]==this.value){B=[]}if(this.options.numResults){return B.slice(0,this.options.numResults)}return B},getRegex:function(){var B=this.escapeRegex(this.value);var A=this.regexToString(this.options.beforeMatch).first();return new RegExp(A+B,"i")},getTokens:function(){var F=this.element.getValue();var G=[];if(this.options.multivalue){var C=this.regexToString(this.options.tokenSplitter);var E=C.first();var B=C.last();if(!B.match(/g/)){B+="g"}var D=F.split(this.options.tokenSplitter);var A=F.match(new RegExp(E,B))||[];D.each(function(I,H){G.push(I);if(A[H]){G.push(A[H])}})}else{G.push(F)}return G},markPrevious:function(){if(this.selectedIndex<0){return}this.selectedIndex-=1;this.updateSelected()},markNext:function(){if(this.selectedIndex==this.matches.length){return}this.selectedIndex+=1;this.updateSelected()},selectEntry:function(){var B=this.getSelectedValue();this.reset();if(!B){return false}var A=this.getTokens();A=A.slice(0,A.length-1);B=A.join("")+B;if(this.options.multivalue&&this.options.transformSeparator){B+=this.options.transformSeparator}this.element.setValue(B);return true},escapeRegex:function(A){return A.replace(/([.*+?|(){}[\]\\])/g,"\\$1")},regexToString:function(B){var A=B.toString();var C=A.match(/^\/(.*)\/(\w*)$/);return[C[1],C[2]]}});var ModalDialog=Class.create({initialize:function(B,A){this.options=A||{};this.createElements();this.updateContent(B)},createElements:function(){if(this.blackout){this.blackout.remove()}this.blackout=new Element("div");this.blackout.addClassName("blackout");this.blackout.setStyle({position:"absolute",display:"none",background:"black"});if(this.container){this.container.remove()}this.container=new Element("div");this.container.addClassName("dialog_container");this.container.setStyle({position:"absolute",display:"none"});var A=$("body");A.appendChild(this.blackout);A.appendChild(this.container)},position:function(){var C=this.container.getDimensions();var B=document.viewport.getScrollOffsets();var A=document.viewport.getDimensions();var E=(A.height/4)-(C.height/4)+B.top;var D=(A.width/2)-(C.width/2)+B.left;this.blackout.setStyle({top:B.top+"px",left:B.left+"px",width:"100%",height:"100%"});this.container.setStyle({left:D+"px",top:E+"px"})},updateContent:function(A){if(Object.isString(A)){this.container.innerHTML=A}else{this.container.innerHTML="";this.container.appendChild(A)}this.container.select(".hide_dialog").each(function(B){B.observe("click",this.onClickHide.bind(this))},this);this.position()},onClickHide:function(A){A.stop();this.hide()},onScroll:function(A){this.position()},show:function(){if(this.effecting){return}this.effecting=true;this.boundOnScroll=this.onScroll.bind(this);Event.observe(window,"scroll",this.boundOnScroll);this.position();new Effect.Parallel([new Effect.Appear(this.blackout,{from:0,to:0.2,sync:true}),new Effect.Appear(this.container,{sync:true})],{duration:0.25,afterFinish:this.doShow.bind(this)})},doShow:function(){this.effecting=false;this.afterShown()},afterShown:function(){if(this.options.afterShown){this.options.afterShown()}},hide:function(){if(this.effecting){return}this.effecting=true;if(this.boundOnScroll){Event.stopObserving(window,"scroll",this.boundOnScroll);this.boundOnScroll=null}new Effect.Parallel([new Effect.Fade(this.blackout,{sync:true}),new Effect.Fade(this.container,{sync:true})],{duration:0.25,afterFinish:(function(){this.effecting=false}).bind(this)})}});ModalDialog.Ajax=Class.create({initialize:function(B,A){if(B.match("a")){this.href=B.href;this.method="get"}else{if(B.match("input")){var C=B.up("form");this.href=C.action;this.method=C.method}}B.observe("click",this.onClickShow.bind(this));this.options=A||{}},createDialog:function(){var A=new Element("div");A.addClassName("loading");this.dialog=new ModalDialog(A,this.options)},onClickShow:function(A){A.stop();if(!this.dialog){this.createDialog()}this.dialog.show();if(!this.isLoaded){this.load()}},load:function(){if(!this.isLoading){this.isLoading=true;new Ajax.Request(this.href,{method:this.method,onSuccess:this.doLoad.bind(this),onComplete:(function(A){this.isLoading=false}).bind(this)})}},doLoad:function(A){this.dialog.updateContent(A.responseText);this.dialog.afterShown();this.isLoaded=true}});var TaskRow=Class.create({initialize:function(A,B){this.editEventsWired=false;if(B){this.editRow=B;if(!A||this.editRow.visible()){this.wireEditingEvents()}}if(A){this.viewRow=A;this.wireViewingEvents();this.wireDragging();this.wireSorting()}this.boundOnOtherTaskEditing=this.onOtherTaskEditing.bind(this);Tasks.table.observe(Tasks.TASK_EDITING_EVENT,this.boundOnOtherTaskEditing);this.boundOnIdentifyByRow=this.onIdentifyByRow.bind(this);Tasks.table.observe(Tasks.TASK_IDENTIFY_BY_ROW_EVENT,this.boundOnIdentifyByRow)},wireViewingEvents:function(){this.editLink=this.viewRow.select(".edit>a.edit")[0];this.editLink.observe("click",this.onClickEdit.bind(this));this.trashcan=this.viewRow.select(".cancel>a.delete")[0];this.trashcan.observe("click",this.onClickTrash.bind(this));var A=this.viewRow.select(".complete")[0];A.observe("click",this.onClickComplete.bind(this));this.viewRow.observe("dblclick",this.onDoubleClickViewRow.bind(this));Tasks.table.observe(Tasks.TASKS_DRAGGABLE_EVENT,this.onTasksDraggable.bind(this));Tasks.table.observe(Tasks.TASKS_NOT_DRAGGABLE_EVENT,this.onTasksNotDraggable.bind(this))},wireEditingEvents:function(){var A=this.editRow.select(".edit>input[type=submit]")[0];A.observe("click",this.onClickSave.bind(this));this.editRow.observe("keydown",this.onKeyDown.bind(this));this.cancelLink=this.editRow.select(".cancel>a.cancel")[0];this.boundOnClickCancel=this.onClickCancel.bind(this);this.cancelLink.observe("click",this.boundOnClickCancel);this.wireProjectAutocomplete();this.wireContextAutocomplete();this.editEventsWired=true},wireDragging:function(){this.dragger=new Draggable(this.viewRow,{starteffect:null,endeffect:null,revert:true,ghosting:false,constraint:"vertical",onStart:this.onStartDrag.bind(this),onEnd:this.onStopDrag.bind(this),onDrag:this.onDrag.bind(this)})},wireSorting:function(){this.boundOnSortRequest=this.onSortRequest.bind(this);Tasks.table.observe(Tasks.TASK_REQUEST_SORT_EVENT,this.boundOnSortRequest);var A=$F(this.editRow.select("td.due>input").first()).split("/");A=(A.length<3)?"":A[2]+" "+A[0]+" "+A[1];this.sorting={done:this.isCompleted()?"t":"f",project:$F(this.editRow.select("td.project>input").first()),task:$F(this.editRow.select("td.task>input").first()),context:$F(this.editRow.select("td.context>input").first()),due:A,createdAt:parseInt($F(this.editRow.select("input.created_at").first()))}},wireProjectAutocomplete:function(B){var A=this.editRow.select("td.project>input").first();new InstantAutocompleter(A,function(){return DNZO.projects},{numResults:5})},wireContextAutocomplete:function(A){var B=this.editRow.select("td.context>input").first();new InstantAutocompleter(B,function(){return DNZO.contexts},{numResults:5,multivalue:true,tokenSplitter:/[^\w\d@_-]+/,beforeMatch:/(^|\s|@)/,transformSeparator:" ",continueTabOnSelect:false})},destroy:function(){if(this.viewRow){this.viewRow.remove()}if(this.editRow&&this.editRow.parentNode){this.editRow.remove()}this.ignoreCancels()},ignoreCancels:function(){Event.stopObserving(Tasks.table,Tasks.TASK_EDITING_EVENT,this.boundOnOtherTaskEditing);if(this.boundOnSortRequest){Event.stopObserving(Tasks.table,Tasks.TASK_REQUEST_SORT_EVENT,this.boundOnSortRequest)}Event.stopObserving(Tasks.table,Tasks.TASK_IDENTIFY_BY_ROW_EVENT,this.boundOnIdentifyByRow);Event.stopObserving(this.cancelLink,"click",this.boundOnClickCancel);this.cancelLink.hide();this.editRow.select("input").each(function(A){A.disable()})},unignoreCancels:function(){Tasks.table.observe(Tasks.TASK_EDITING_EVENT,this.boundOnOtherTaskEditing);if(this.boundOnSortRequest){Tasks.table.observe(Tasks.TASK_REQUEST_SORT_EVENT,this.boundOnSortRequest)}Tasks.table.observe(Tasks.TASK_IDENTIFY_BY_ROW_EVENT,this.boundOnIdentifyByRow);this.cancelLink.observe("click",this.boundOnClickCancel);this.cancelLink.show();this.editRow.select("input").each(function(A){A.enable()})},onSortRequest:function(A){(A.memo||[]).push(this)},removeRows:function(){if(this.editRow){this.editRow.remove()}if(this.viewRow){this.viewRow.remove()}},addRowsBefore:function(A){if(this.editRow){Insertion.Before(A,this.editRow)}if(this.viewRow){Insertion.Before(A,this.viewRow)}},compareTo:function(B,D,F){var C=this.sorting[D]||"";var A=B.sorting[D]||"";if(typeof F=="undefined"){F=false}if(!D||DNZO.strcmp(C,A)==0){return this.sorting.createdAt-B.sorting.createdAt}var E=DNZO.strcmp(C,A);if(F){E*=-1}return E},taskID:function(){var A=this.viewRow&&this.viewRow.select("input.task-id").first();if(A){return A.getValue()}return null},isEditing:function(){return this.editRow&&this.editRow.visible()},isCompleted:function(){return this.viewRow&&this.viewRow.hasClassName("completed")},fire:function(B,A){Event.fire((this.viewRow||this.editRow),B,A)},findTaskAbove:function(){var A=this.viewRow.previousSiblings().find(function(B){return B.match("tr.task-row")&&!B.hasClassName("editable")});return Tasks.taskFromRow(A)},findTaskBelow:function(){var A=this.viewRow.nextSiblings().find(function(B){return B.match("tr.task-row")&&!B.hasClassName("editable")});return Tasks.taskFromRow(A)},onClickEdit:function(A){A.stop();this.edit();this.activate()},onClickCancel:function(A){A.stop();this.cancel()},onClickTrash:function(A){A.stop();this.trash()},onClickSave:function(D){var E={x:D.pointerX(),y:D.pointerY()};if(E.x!=0||E.y!=0){var B=D.element();var C=B.getDimensions();var A=B.cumulativeOffset();inX=E.x>=A.left&&E.x<=A.left+C.width;inY=E.y>=A.top&&E.y<=A.top+C.height;if(inX&&inY){this.save()}}D.stop()},onClickComplete:function(C){if(this.isEditing()){return}var A=C.element();var B=A.checked;this.completeOrUncomplete(B)},onDoubleClickViewRow:function(C){C.stop();var A=C.element();var D=(A.match("td"))?A:A.up("td");var B=null;if(D){B=D.classNames().toArray().first();if(["done","edit","cancel"].include(B)){return}}this.edit();this.activate(B)},onKeyDown:function(A){switch(A.keyCode){case Event.KEY_RETURN:this.save();A.stop();break;case Event.KEY_ESC:this.cancel();A.stop();break}},onOtherTaskEditing:function(A){if(this.isEditing()){this.cancel()}},onIdentifyByRow:function(A){var B=A.memo&&A.memo.row;if(B&&(this.viewRow==B||this.editRow==B)){A.memo.task=this}A.stop()},onTasksDraggable:function(A){this.wireDragging(this.viewRow)},onTasksNotDraggable:function(A){if(this.dragger){this.dragger.destroy();this.dragger=null}},onStartDrag:function(A,B){this.viewRow.addClassName("dragging");this.viewRow.up("table").addClassName("row-dragging");this.recordPosition();this.findDragBounds()},onStopDrag:function(A,B){this.viewRow.removeClassName("dragging");this.viewRow.up("table").removeClassName("row-dragging");this.savePosition()},onDrag:function(A,F){var E=document.viewport.getScrollOffsets().top;var G=F.clientY+E;var D,B=null;var C=0;if(this.canMoveUp&&G<this.topDragBounds.first()){if(this.topDragBounds.length>1){B=this.topDragBounds.find(function(H){return G>H});C=B?this.topDragBounds.indexOf(B)-1:this.topDragBounds.length-1}D=this.aboveNeighbors[C];this.moveUp(D)}else{if(this.canMoveDown&&G>this.bottomDragBounds.first()){if(this.bottomDragBounds.length>1){B=this.bottomDragBounds.find(function(H){return G<H});C=B?this.bottomDragBounds.indexOf(B)-1:this.bottomDragBounds.length-1}D=this.belowNeighbors[C];this.moveDown(D)}}},findDragBounds:function(){var B=function(C){return C.match("tr.task-row")&&C.visible()};this.aboveNeighbors=this.viewRow.previousSiblings().findAll(B);this.belowNeighbors=this.viewRow.nextSiblings().findAll(B).reject(function(C){return C.hasClassName("unsaved")});var A=this.viewRow.getDimensions().height;this.canMoveUp=this.aboveNeighbors.length>0;this.topDragBounds=null;if(this.canMoveUp){this.topDragBounds=this.aboveNeighbors.collect(function(D){var C=D.getDimensions().height;return D.cumulativeOffset().top+C-(C>A?C-A:0)})}this.canMoveDown=this.belowNeighbors.length>0;this.bottomDragBounds=null;if(this.canMoveDown){this.bottomDragBounds=this.belowNeighbors.collect(function(C){return C.cumulativeOffset().top})}},moveUp:function(A){var B=A.hasClassName("editable")?A:A.previousSiblings()[0];this.moveAboveRow(B);this.findDragBounds()},moveDown:function(A){var B=A.hasClassName("editable")?A.nextSiblings()[1]:A.nextSiblings()[0];this.moveAboveRow(B);this.findDragBounds()},moveAboveRow:function(A){this.viewRow.remove();this.editRow.remove();A.parentNode.insertBefore(this.editRow,A);A.parentNode.insertBefore(this.viewRow,A)},edit:function(){if(this.isCompleted()){return}this.fire(Tasks.TASK_EDITING_EVENT);if(!this.editEventsWired){this.wireEditingEvents(this.editRow)}this.viewRow.hide();this.editRow.show();this.activate()},cancel:function(){this.fire(Tasks.TASK_CANCEL_EDITING_EVENT);if(this.viewRow){this.viewRow.show();this.editRow.hide()}else{this.destroy()}},trash:function(){if(!this.requestedTrash){this.requestedTrash=true;this.viewRow.hide();new Ajax.Request(this.trashcan.href,{method:"get",onComplete:this.bindOnComplete({onSuccess:this.doTrash,onFailure:function(A){this.viewRow.show()},onComplete:function(A){this.requestedTrash=false}})})}},doTrash:function(A){Tasks.updateStatusFromResponse(A);this.destroy()},save:function(){if(!this.isSaving){this.isSaving=true;var A=null;if(this.viewRow){A=this.editLink.href}Tasks.saveTask(A,this.editRow,{onComplete:this.bindOnComplete({onSuccess:this.doSave,onFailure:function(B){this.unignoreCancels();this.cancel()},onComplete:function(B){this.isSaving=false}})});this.ignoreCancels();this.fire(Tasks.TASK_SAVED_EVENT,this.editRow)}},doSave:function(B){var A=this.replaceRows(B);if(!A){Tasks.showError("TASKS_LIMIT_ERROR");this.destroy()}},completeOrUncomplete:function(A){var C={};var B=this.editRow&&this.editRow.select("input.complete").first();if(B){B.checked=A}if(A){C.force_complete=true;this.viewRow.addClassName("completed");this.sorting.done="t"}else{C.force_uncomplete=true;this.viewRow.removeClassName("completed");this.sorting.done="f"}new Ajax.Request(this.editLink.href,{method:"post",parameters:C,onComplete:this.bindOnComplete()})},recordPosition:function(){var A=this.position;this.taskAbove=this.findTaskAbove();this.taskBelow=this.findTaskBelow();this.position={task_above:this.taskAbove&&this.taskAbove.taskID(),task_below:this.taskBelow&&this.taskBelow.taskID()};return Object.toJSON(A||{})!=Object.toJSON(this.position)},savePosition:function(){if(this.recordPosition()){var C=this.sorting.createdAt;var A=this.taskAbove&&this.taskAbove.sorting.createdAt;var D=this.taskBelow&&this.taskBelow.sorting.createdAt;if(!D){var B=new Date();C=(B.getTime()-(B.getTimezoneOffset()*60))*1000}else{if(!A){C=D-100}else{C=A+parseInt((D-A)/2)}}this.sorting.createdAt=C;new Ajax.Request(this.editLink.href,{method:"post",onComplete:this.bindOnComplete({}),parameters:this.position})}},bindOnComplete:function(A){A=A||{};return function(C){if(!C.status||C.status==0){return}var B=true;if(C.status==200){if(!C.responseText||C.responseText.indexOf("task-ajax-response")<0){Tasks.showError("LOGGED_OUT_ERROR");B=false}}else{if(C.status==302){Tasks.showError("LOGGED_OUT_ERROR");B=false}else{Tasks.doFail(C);B=false}}if(B){if(A.onSuccess){A.onSuccess.bind(this)(C)}}else{if(A.onFailure){A.onFailure.bind(this)(C)}}(A.onComplete||Prototype.emptyFunction).bind(this)(C)}.bind(this)},replaceRows:function(F){var B=this.editRow.parentNode;var A=Tasks.containerFromResponse(F);var D=A.select("tr");if(D.length<2){return false}if(this.viewRow){this.viewRow.remove()}var E=D.find(function(G){return G.hasClassName("editable")});var C=D.without(E)[0];B.insertBefore(E,this.editRow);B.insertBefore(C,this.editRow);this.editRow.remove();this.initialize(C,E);return true},activate:function(B){if(!this.editRow){return}if(!B){var A=this.editRow.select("td.task>input").first();var E=this.editRow.select("td.project>input").first();if(A&&E){var D=E.getDimensions().width>0;if(A.getValue().blank()&&E.getValue().blank()&&D){E.activate()}else{A.activate()}}}else{var C=this.editRow.select("td."+B+">input").first();if(C){C.activate()}}}});var Tasks={TASK_SAVED_EVENT:"tasks:task_saved",TASK_EDITING_EVENT:"tasks:task_editing",TASK_CANCEL_EDITING_EVENT:"tasks:task_cancel_editing",TASK_IDENTIFY_BY_ROW_EVENT:"tasks:task_identify",TASK_REQUEST_SORT_EVENT:"tasks:request_sort",TASKS_DRAGGABLE_EVENT:"tasks:draggable",TASKS_NOT_DRAGGABLE_EVENT:"tasks:not_draggable",HIDE_STATUS_DELAY:15,load:function(B){Tasks.table=$("tasks_list");if(!Tasks.table||Tasks.table.hasClassName("archived")){return}new ModalDialog.Ajax($("add_list"),{afterShown:function(){var D=$("new_list_name");if(D){D.activate()}}});Tasks.addRow=Tasks.table.select("#add_row")[0];Tasks.tasksForm=$("tasks_form");Tasks.newTaskTableHTML=Tasks.tasksForm.innerHTML;Tasks.addRow.observe("click",Tasks.onClickAddTask);Tasks.wireSortingEvents();var C=Tasks.table.select("tr.task-row");for(var A=0;A<C.length;A+=2){new TaskRow(C[A+1],C[A])}Tasks.setHideStatus();Tasks.wireHistory()},wireSortingEvents:function(){Tasks.table.select("th>a").each(function(A){A.observe("click",Tasks.onClickSort)})},wireHistory:function(){Tasks.onHistoryChange();History.Observer.observe("all",Tasks.onHistoryChange);History.Observer.start()},addHistoryEvent:function(A){History.setMultiple(A)},draggable:function(){return Tasks.table.hasClassName("draggable")},onHistoryChange:function(A){Tasks.sort(History.get("order"),History.get("descending"))},onClickSort:function(C){C.stop();var B=C.element();B=B.match("a")?B:B.up("a");var E=B.up("th");var A=B.href.match(/order=([\w_]+)/)[1];var F=false;if(E.match(".sorted.descending")){A=null}else{if(E.match(".sorted")){F=true}}var D={order:A||""};if(A&&F){D.descending=true}else{D.descending=null}Tasks.addHistoryEvent(D);Tasks.sort(A,F)},sort:function(A,C){Tasks.cancelAll();Tasks.table.select("th").each(function(D){["sorted","descending"].each(function(E){D.removeClassName(E)});if(D.hasClassName(A)){D.addClassName("sorted");if(C){D.addClassName("descending")}}});var B=Event.fire(Tasks.table,Tasks.TASK_REQUEST_SORT_EVENT,[]).memo;B.sort(function(E,D){return E.compareTo(D,A,C)});B.each(function(D){D.removeRows();D.addRowsBefore(Tasks.addRow)});if(A&&Tasks.table.hasClassName("draggable")){Event.fire(Tasks.table,Tasks.TASKS_NOT_DRAGGABLE_EVENT);Tasks.table.removeClassName("draggable")}else{if(!A){Event.fire(Tasks.table,Tasks.TASKS_DRAGGABLE_EVENT);Tasks.table.addClassName("draggable")}}},taskFromRow:function(B){var A=Event.fire(Tasks.table,Tasks.TASK_IDENTIFY_BY_ROW_EVENT,{row:B});return A.memo.task},onClickAddTask:function(A){A.stop();Tasks.cancelAll();Tasks.doAddNewTask(Tasks.getNewTaskRow(),A.memo)},addCanceled:function(A){Tasks.addRow.show();Event.stopObserving(Tasks.table,Tasks.TASK_SAVED_EVENT,Tasks.addSaved);A.stop()},addSaved:function(A){Tasks.onClickAddTask(A)},doAddNewTask:function(D,A){var C=Tasks.table.select("tbody")[0];Tasks.addRow.remove();C.insert(D);C.insert(Tasks.addRow);if(A){["context","project"].each(function(G){var E="td."+G+">input";var F=A.select(E).first();var H=D.select(E).first();if(H&&F){H.setValue(F.getValue())}})}var B=new TaskRow(null,D);Tasks.table.observe(Tasks.TASK_SAVED_EVENT,Tasks.addSaved);D.observe(Tasks.TASK_CANCEL_EDITING_EVENT,Tasks.addCanceled);Tasks.addRow.hide();B.activate()},cancelAll:function(){Event.fire(Tasks.table,Tasks.TASK_EDITING_EVENT)},loadStatus:function(B){var A=B.select("div").find(function(D){return D.id=="status"});if(!A){return}var C=$("status");if(C){C.innerHTML=A.innerHTML;A=C}else{A.hide();Tasks.table.up("div").appendChild(A)}Tasks.showStatus();Tasks.setHideStatus()},setHideStatus:function(){if(Tasks.hideStatusTimeout){clearTimeout(Tasks.hideStatusTimeout)}Tasks.hideStatusTimeout=setTimeout(Tasks.hideStatus,Tasks.HIDE_STATUS_DELAY*1000)},hideStatus:function(){var A=$("status");if(!A){return}var B=A.immediateDescendants().collect(function(C){return new Effect.Fade(C,{sync:true})});new Effect.Parallel(B,{duration:0.1,afterFinish:function(){new Effect.BlindUp(A,{duration:0.1})}})},showStatus:function(){var A=$("status");if(!A||A.visible()){return}var B=A.immediateDescendants().collect(function(C){C.hide();return new Effect.Appear(C,{sync:true})});new Effect.BlindDown(A,{duration:0.1,afterFinish:function(){new Effect.Parallel(B,{duration:0.1})}})},updateStatusFromResponse:function(A){Tasks.loadStatus(Tasks.containerFromResponse(A))},updateProjects:function(B){var A=B.select("td.project>input").first();A=A&&A.getValue();if(!A){return}DNZO.projects=[A,DNZO.projects.without(A)].flatten()},updateContexts:function(A){var B=A.select("td.context>input").first();B=B&&B.getValue();if(!B){return}B.split(/[,;\s]+/).each(function(C){C=C.replace(/[^\w\s-]/,"").strip().toLowerCase();C="@"+C.replace(/[-\s]+/,"-");DNZO.contexts=[C,DNZO.contexts.without(C)].flatten()})},saveTask:function(E,F,B){var C=function(L,K,G){var J=L.select(G);var H=K.select(G);if(J.length!=H.length){return}var I=0;J.each(function(M){H[I].setValue(M.getValue());I+=1})};C(F,Tasks.tasksForm,"input[type=text]");var A="input[type=checkbox]";Tasks.tasksForm.select(A)[0].checked=F.select(A)[0].checked;var D=Tasks.tasksForm.action;Tasks.tasksForm.action=E?E:D;Tasks.tasksForm.request(B);Tasks.tasksForm.action=D;Tasks.updateProjects(F);Tasks.updateContexts(F)},getNewTaskRow:function(){var A=new Element("div");A.innerHTML=Tasks.newTaskTableHTML;return A.select("tr")[0]},containerFromResponse:function(B){var A=new Element("div");A.innerHTML=B.responseText;return A},showError:function(E){if(typeof E=="undefined"){E="DEFAULT_ERROR"}var A=new Element("div",{className:"error_dialog dialog_content"});var B=new Element("h2");B.innerHTML="Whoops!";A.appendChild(B);var C=new Element("ul");A.appendChild(C);DNZO.Messages[E].split("\n").each(function(G){var F=new Element("li");F.innerHTML=G;C.appendChild(F)});var D=new Element("li",{className:"buttons"});D.appendChild(new Element("input",{type:"submit",value:"OK",className:"hide_dialog"}));C.appendChild(D);(new ModalDialog(A)).show()},doFail:function(A){Tasks.showError()}};Event.observe(window,"load",Tasks.load);