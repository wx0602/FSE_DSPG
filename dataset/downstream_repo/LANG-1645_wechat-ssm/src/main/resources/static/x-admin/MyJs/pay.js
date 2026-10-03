var pageUrl = "/pay/page2Custom.html";
var updateUrl = "/kindergarten/update.html";

$(function(){
	queryFY();
});

/**
 * 填充表格数据
 * @param pageInfo  ajax返回的参数信息
 */
function showTable(pageInfo) {
    var total = pageInfo.total;//总数
    var pageNum = pageInfo.pageNum;;//页号
    var pageSize = pageInfo.pageSize;//页大小

    var beans = pageInfo.list;
    $("#tbody").html("");//清空表格中数据并重新填充数据
    for(var i=0,length_1 = beans.length;i<length_1;i++){
        var index = (pageNum - 1) * pageSize + i + 1;
        var tr = "<tr>"
            +'<td>'+index+'</td>'
            +'<td>'+replaceNull(beans[i].kindergartenName)+'</td>'
            +'<td>'+replaceNull(beans[i].childrenName)+'</td>'
            +'<td>'+replaceNull(beans[i].wechataddress)+'</td>'
            +'<td>'+replaceNull(beans[i].parentName)+'</td>'
            +'<td>'+replaceNull(beans[i].parentPhone)+'</td>'
            +'<td>'+replaceNull(beans[i].payDate)+'</td>'
            +'<td>'+replaceNull(beans[i].payAmount)+'</td>'
            +'<td>'+replaceNull(beans[i].remark1)+'</td>'
            +'<td>'+replaceNull(beans[i].orderId)+'</td>'
            +'<td>'+replaceNull(beans[i].orderStatus)+'</td>';
/*	        if(isAdmin()){
  				tr += '<td><a href=javascript:void(0) title="删除" onclick="remove(\''+beans[i].id+'\')"><i class="layui-icon">&#xe640;</i></a></td>'
	        }*/
            
        	tr +='</tr>'
        		
        $("#tbody").append(tr);
    }

    //开启分页组件
    showPage(total, pageNum, pageSize);
}