function checkClicks(){
    let checks = document.getElementsByClassName('checks');
    let count = 0;
    for(let i=0; i<checks.length; i++){
        if(checks[i].checked === true){
            count += 1
            document.getElementById('trash-button').style.display = 'block'
        }
        if(count > 1){
            document.getElementById('merge-button').style.display = 'block'
            break
        }
    }
    if(count === 1){
        document.getElementById('merge-button').style.display = 'none'
    }
    if(count === 0){
        document.getElementById('trash-button').style.display = 'none'
    }
}

function checkBoxTrash(){
    let checks = document.getElementsByClassName('checks');
    let ids = [];
    for(let i=0; i<checks.length; i++){
        if(checks[i].checked === true){
            ids.push(checks[i].value)
        }
    }
    deleteRecord(ids.join(','))
}

function checkBoxMerge(){
    let checks = document.getElementsByClassName('checks');
    let ids = [];
    for(let i=0; i<checks.length; i++){
        if(checks[i].checked === true){
            ids.push(checks[i].value)
        }
    }
    window.location.replace("/manual-merge?ids=" + ids.join(','))
}

function hideManMerge(){
    window.location.replace("/")
}

function tailorSuggestion(type){
    let form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    let input = document.createElement('input');
    input.type = 'hidden';
    let ints = document.getElementById('ints');
    input.name = 'ints';
    input.value = ints.innerText;
    if (type === 'remove'){
        form.action = '/tailor?type=remove';
    }
    else{
        let input2 = document.createElement('input');
        input2.type = 'hidden';
        let hgvs = document.getElementById('hgvs');
        input2.name = 'hgvs';
        input2.value = hgvs.innerText;
        form.action = '/tailor?type=update';
        form.appendChild(input2);
    }
    form.appendChild(input);
    form.submit();
}

function restore(id){
    window.location.replace("/empty?type=restore&id=" + id)
}
function permanent(){
    let id = document.getElementById('entry-id');
    window.location.replace("/empty?type=permanent&id=" + id.innerText)
}
function deleteRecord(id){
    window.location.replace("/trash?id=" + id)
}

function mergeDupModal(visible,hgvs,ids){
    if (visible === 'show'){
        let tr = document.getElementById(hgvs);
        cancel = false
        row = ''
        for(let i = 0; i < tr.children.length; i++){
            if(tr.children[i].children[0].innerHTML === ''){
                cancel = true
                alert('All fields must have a value in order to merge.')
                break
            }
            else{
                row += tr.children[i].children[0].innerHTML + ','
            }
        }
        if (!cancel){
            document.getElementById('merge-dup-modal').style.display = 'block';
            row = row.replaceAll('&gt;','>')
            row = row.replaceAll('&lt;','<')
            row = row.slice(0,-1)
            let form = document.createElement('form');
            form.method = 'post';
            form.action = '/dup-merge';
            document.body.appendChild(form);
            let input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'update';
            input.value = row;
            form.appendChild(input);
            let trash_ids = document.createElement('input');
            trash_ids.type = 'hidden';
            trash_ids.name = 'trash';
            let id = tr.children[0].children[0].innerHTML;
            let id_list = ids.split(',');
            for (let i = 0; i < id_list.length; i++){
                if (id_list[i] === id){
                    id_list.splice(i, 1);
                    document.getElementById('dup-updated-id').innerHTML = id
                }
            }
            document.getElementById('dup-removed-id').innerHTML = id_list.join()
            trash_ids.value = id_list.join();
            form.appendChild(trash_ids);
            let button = document.getElementById('dup-confirm');
            button.onclick = function(){
                form.submit()
            }
        }
    }
    else{
        document.getElementById('merge-dup-modal').style.display = 'none';
    }
}

function removeDupMerge(hgvs){
    let form = document.createElement('form');
    form.method = 'post';
    form.action = '/remove-dup-merge';
    document.body.appendChild(form);
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'hgvs';
    input.value = hgvs;
    form.appendChild(input);
    form.submit()
}

function removeSynMerge(unique){
    let form = document.createElement('form');
    form.method = 'post';
    form.action = '/remove-syn-merge';
    document.body.appendChild(form);
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'unique';
    input.value = unique;
    form.appendChild(input);
    form.submit()
}

function mergeSynModal(visible,name,ids){
    if (visible === 'show'){
        let tr = document.getElementById(name);
        cancel = false
        row = ''
        for(let i = 0; i < tr.children.length; i++){
            if(tr.children[i].children[0].innerHTML === ''){
                cancel = true
                alert('All fields must have a value in order to merge.')
                break
            }
            else{
                row += tr.children[i].children[0].innerHTML + ','
            }
        }
        if (!cancel){
            document.getElementById('merge-syn-modal').style.display = 'block';
            row = row.replaceAll('&gt;','>')
            row = row.replaceAll('&lt;','<')
            row = row.slice(0,-1)
            let form = document.createElement('form');
            form.method = 'post';
            form.action = '/syn-merge';
            document.body.appendChild(form);
            let input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'update';
            input.value = row;
            form.appendChild(input);
            let trash_ids = document.createElement('input');
            trash_ids.type = 'hidden';
            trash_ids.name = 'trash';
            let id = tr.children[0].children[0].innerHTML;
            let id_list = ids.split(',');
            for (let i = 0; i < id_list.length; i++){
                if (id_list[i] === id){
                    id_list.splice(i, 1);
                    document.getElementById('syn-updated-id').innerHTML = id
                }
            }
            document.getElementById('syn-removed-id').innerHTML = id_list.join()
            trash_ids.value = id_list.join();
            form.appendChild(trash_ids);
            let button = document.getElementById('syn-confirm');
            button.onclick = function(){
                form.submit()
                showLoading();
            }
        }
    }
    else{
        document.getElementById('merge-syn-modal').style.display = 'none';
    }
}

function singleSuggestion(type){
    let form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    let input = document.createElement('input');
    input.type = 'hidden';
    if(type === 'remove'){input.type = 'hidden';
        let id = document.getElementById('entry-id');
        input.name = 'entry-id';
        input.value = id.innerText;
        form.action = '/remove-suggestion';
    }
    else{
        let hgvs = document.getElementById('hgvs');
        input.name = 'hgvs';
        input.value = hgvs.innerText;
        form.action = '/accept-suggestion';
    }
    form.appendChild(input);
    form.submit();
}

function merge(hgvs,id,col){
    let td = document.getElementById(id)
    let tr = document.getElementById(hgvs);
    tr.children[parseInt(col)].innerHTML = "<div style=\"text-align: center;\">" + td.children[1].innerHTML + "</div>"
}

function mergeSyn(unique,id,col,vrs,ncol){
    let td = document.getElementById(id)
    let tr = document.getElementById(unique);
    tr.children[parseInt(col)].innerHTML = "<div style=\"text-align: center;\">" + td.children[1].innerHTML + "</div>"
    if (vrs !== ''){
        tr.children[parseInt(ncol) - 1].innerHTML = "<div style=\"text-align: center;\">" + vrs + "</div>"
    }
}

function newEdit(){
    document.getElementById("save-edit").style.display = 'inline';
    document.getElementById("cancel-edit").style.display = 'inline';
}

function saveEdit(id){
    showLoading();
    let row = '';
    document.getElementById(id).childNodes.forEach((item, i) => {
        inner = item.innerHTML;
        if(inner){
            if(inner.includes('div')){
                let div_content = inner.split('contenteditable="">')[1].split('</div')[0] + ',';
                //Pasted edits
                if(div_content.includes('pre')){
                    row += div_content.split('>')[1].split('<')[0] + ',';
                }
                //Manually-typed edits
                else{
                    row += div_content
                }
            }
            else{
                row += inner + ','
            }
        }
    });
    row = row.slice(0,-1)
    let form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = '/save';
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'row';
    input.value = row;
    form.appendChild(input);
    form.submit();
}

function select(id){
    window.location.replace("/detail?id=" + id)
}

function back(){
    window.location.replace("/")
}

function newEntry(){
    document.getElementById('add-row').style.display = 'block'
}

function closeEntry(){
    document.getElementById('add-row').style.display = 'none'
}

function modal(warning){
    if (warning === 'True'){
        document.getElementById('modal').style.display = 'block';
    }
}

function trashModal(show,id){
    if (show === 'true'){
        document.getElementById('entry-id').innerText = id;
        document.getElementById('trash-modal').style.display = 'block';
    }
    else{
        document.getElementById('trash-modal').style.display = 'none';
    }
}

function suggestModal(show,type,ints,id,hgvs){
    if (show === 'true'){
        document.getElementById('ints').innerText = ints;
        document.getElementById('entry-id').innerText = id;
        document.getElementById('hgvs').innerText = hgvs;
        document.getElementById(type).style.display = 'block';
    }
    else{
        document.getElementById(type).style.display = 'none';
    }

}

function showInitializing(){
    let non = document.getElementById('non');
    non.style.opacity = "0.1";
    let loading = document.getElementById("initializing");
    loading.style.display = "block";
}

function showLoading(){
    let non = document.getElementById('non');
    non.style.opacity = "0.1";
    let loading = document.getElementById("loading");
    loading.style.display = "block";
}

function hideLoading(){
    let non = document.getElementById('non');
    non.style.opacity = "1";
    let loading = document.getElementById("loading");
    loading.style.display = "none";
}

function highlight(selected){
    if(selected.includes('|')){
        let t = selected.split('|')[1]
        let nav = document.getElementById('suggestion-tabs');
        let tabs = nav.getElementsByTagName('li');
        for (let i = 0; i < tabs.length; i++){
            tabs[i].childNodes[1].classList.remove('active')
            if (tabs[i].id === t){
                tabs[i].childNodes[1].classList.add('active');
            }
        }
        selected = selected.split('|')[0]
    }
    document.getElementById('table-load').style.display = 'none';
    let list = document.getElementById('sidebar-list');
    let items = list.getElementsByTagName('li');
    for (let i = 0; i < items.length; i++){
        items[i].childNodes[1].classList.remove('active')
        if (items[i].id === selected){
            items[i].childNodes[1].classList.add('active');
        }
    }
    list = document.getElementById('report-list');
    items = list.getElementsByTagName('li');
    for (i = 0; i < items.length; i++){
        items[i].childNodes[1].classList.remove('active')
        if (items[i].id === selected){
            items[i].childNodes[1].classList.add('active');
        }
    }
    list = document.getElementById('about-list');
    items = list.getElementsByTagName('li');
    for (i = 0; i < items.length; i++){
        items[i].childNodes[1].classList.remove('active')
        if (items[i].id === selected){
            items[i].childNodes[1].classList.add('active');
        }
    }
    //hideLoading()
}

function buildColSelect(colnames){
    if (colnames !== ''){
        cc = colnames.split(',')
        let div = document.getElementById('cols');
        let inner = '<label for="hgvsSelect">Which column contains the full HGVS expressions? (ex: NM_001171.5:c.1091C>G)</label>'
        inner += '<select class="form-control col-select mb-3" name="hgvsSelect">'
        for (let i = 0; i < cc.length; i++){
            inner += '<option>' + cc[i] + '</option>'
        }
        inner += '</select>'
        inner += '<label for="intSelect">Which column contains the interpretations of the variants?</label>'
        inner += '<select class="form-control col-select" name="intSelect">'
        for (let i = 0; i < cc.length; i++){
            inner += '<option>' + cc[i] + '</option>'
        }
        inner += '</select>'
        inner += '<button class="btn btn-small btn-success mt-3" onclick="this.form.submit();">Load Collection</button>'
        div.innerHTML = inner;
    }
}

function copy(id){
    let copyText = document.getElementById(id).textContent;
    if (copyText === ''){
        console.log('here!');
        copyText = document.getElementById(id).value;
    }
    let textArea = document.createElement('textarea');
    textArea.id = 'temp';
    textArea.textContent = copyText;
    document.body.append(textArea);
    textArea.select();
    document.execCommand("copy");
    /* Alert the copied text */
    alert("Copied to clipboard");
    document.getElementById('temp').remove()
}
