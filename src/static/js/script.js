function tailorSuggestion(){
    let ints = document.getElementById('ints');
    let form = document.createElement('form');
    document.body.appendChild(form);
    form.method = 'post';
    form.action = '/tailor';
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'ints';
    input.value = ints.innerText;
    form.appendChild(input);
    form.submit();
}


function merge(hgvs,id,col){
    let td = document.getElementById(id)
    let table = document.getElementById(hgvs);
    table.children[0].children[0].children[parseInt(col)].innerHTML = "<div style=\"text-align: center;\">" + td.children[1].innerHTML + "</div>"
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
                row += inner.split('>')[1].split('<')[0] + ','
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

function suggestModal(show,type,ints){
    if (show === 'true'){
        document.getElementById('ints').innerText = ints;
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
