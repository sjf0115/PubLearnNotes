package com.sjf.open.utils;

import org.apache.commons.lang3.StringUtils;

/**
 * Created by xiaosi on 17-3-28.
 */
public class ConvertUtil {

    /**
     * 根据vid获取版本 不包含TOUCH
     * @param vid
     * @return
     */
    public static String getPlatform(String vid){

        if(StringUtils.isBlank(vid)){
            return "OTHER";
        }
        if(vid.startsWith("60")){
            return "ADR";
        }
        if(vid.startsWith("80")){
            return "IOS";
        }
        return "OTHER";

    }

    /**
     * 根据vid获取版本 包含TOUCH
     * @param vid
     * @param isTouch
     * @return
     */
    public static String getPlatform(String vid, boolean isTouch){

        if(StringUtils.isBlank(vid)){
            return "OTHER";
        }
        if(isTouch && vid.startsWith("68")){
            return "TOUCH";
        }
        return getPlatform(vid);

    }

    /**
     * String转换为Int
     * @param str
     * @return
     */
    public static int toInt(String str){
        if(StringUtils.isBlank(str)){
            return 0;
        }
        try{
            return Integer.parseInt(str);
        }
        catch (Exception e){
            return 0;
        }
    }

    public static
}
